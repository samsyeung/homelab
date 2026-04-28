// NCCL 4-GPU P2P bandwidth microbench, three modes:
//
//   unidir     — ring 0->1->2->3->0; each rank sends to next, recvs from prev.
//                Reproduces nccl-tests sendrecv_perf -g 4 (~23 GB/s per link).
//   pair_bidir — disjoint pairs 0<->1 and 2<->3, each link used in both
//                directions. Saturates bidirectional PCIe (~47 GB/s per link).
//   ring_bidir — each rank exchanges with BOTH ring neighbours. NCCL collapses
//                to ~1.4 GB/s here — multi-destination per rank doesn't scale
//                on this topology even though all hops are P2P/direct pointer.
//
// Usage:  nccl_p2p_bench MODE [BYTES] [ITERS] [WARMUP]

#include <cuda_runtime.h>
#include <nccl.h>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>

constexpr int NRANKS = 4;

#define CHK_CUDA(x) do { cudaError_t e = (x); if (e != cudaSuccess) { \
    fprintf(stderr, "CUDA %s:%d %s\n", __FILE__, __LINE__, cudaGetErrorString(e)); std::exit(1); } } while (0)
#define CHK_NCCL(x) do { ncclResult_t r = (x); if (r != ncclSuccess) { \
    fprintf(stderr, "NCCL %s:%d %s\n", __FILE__, __LINE__, ncclGetErrorString(r)); std::exit(1); } } while (0)

enum class Mode { Unidir, PairBidir, RingBidir };

static const char* mode_name(Mode m) {
    switch (m) {
        case Mode::Unidir:     return "unidir";
        case Mode::PairBidir:  return "pair_bidir";
        case Mode::RingBidir:  return "ring_bidir";
    }
    return "?";
}

static Mode parse_mode(const char* s) {
    if (!std::strcmp(s, "unidir"))     return Mode::Unidir;
    if (!std::strcmp(s, "pair_bidir")) return Mode::PairBidir;
    if (!std::strcmp(s, "ring_bidir")) return Mode::RingBidir;
    fprintf(stderr, "unknown mode: %s (use unidir|pair_bidir|ring_bidir)\n", s);
    std::exit(2);
}

int main(int argc, char** argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s {unidir|pair_bidir|ring_bidir} [bytes] [iters] [warmup]\n", argv[0]);
        return 2;
    }
    Mode mode   = parse_mode(argv[1]);
    size_t bytes = (argc > 2) ? std::strtoull(argv[2], nullptr, 0) : (256UL << 20);
    int iters   = (argc > 3) ? std::atoi(argv[3]) : 20;
    int warmup  = (argc > 4) ? std::atoi(argv[4]) : 5;

    int devs[NRANKS] = {0, 1, 2, 3};
    ncclComm_t comms[NRANKS];
    cudaStream_t streams[NRANKS];
    void *sn[NRANKS] = {}, *sp[NRANKS] = {}, *rn[NRANKS] = {}, *rp[NRANKS] = {};

    const bool ring_bi = (mode == Mode::RingBidir);

    CHK_NCCL(ncclCommInitAll(comms, NRANKS, devs));
    for (int i = 0; i < NRANKS; i++) {
        CHK_CUDA(cudaSetDevice(i));
        CHK_CUDA(cudaStreamCreate(&streams[i]));
        CHK_CUDA(cudaMalloc(&sn[i], bytes));
        CHK_CUDA(cudaMalloc(&rp[i], bytes));
        if (ring_bi) {
            CHK_CUDA(cudaMalloc(&sp[i], bytes));
            CHK_CUDA(cudaMalloc(&rn[i], bytes));
        }
    }

    auto run = [&]() {
        CHK_NCCL(ncclGroupStart());
        for (int i = 0; i < NRANKS; i++) {
            const int next = (i + 1) % NRANKS;
            const int prev = (i + NRANKS - 1) % NRANKS;
            switch (mode) {
                case Mode::Unidir:
                    CHK_NCCL(ncclSend(sn[i], bytes, ncclChar, next, comms[i], streams[i]));
                    CHK_NCCL(ncclRecv(rp[i], bytes, ncclChar, prev, comms[i], streams[i]));
                    break;
                case Mode::PairBidir: {
                    const int peer = i ^ 1;
                    CHK_NCCL(ncclSend(sn[i], bytes, ncclChar, peer, comms[i], streams[i]));
                    CHK_NCCL(ncclRecv(rp[i], bytes, ncclChar, peer, comms[i], streams[i]));
                    break;
                }
                case Mode::RingBidir:
                    CHK_NCCL(ncclSend(sn[i], bytes, ncclChar, next, comms[i], streams[i]));
                    CHK_NCCL(ncclSend(sp[i], bytes, ncclChar, prev, comms[i], streams[i]));
                    CHK_NCCL(ncclRecv(rn[i], bytes, ncclChar, next, comms[i], streams[i]));
                    CHK_NCCL(ncclRecv(rp[i], bytes, ncclChar, prev, comms[i], streams[i]));
                    break;
            }
        }
        CHK_NCCL(ncclGroupEnd());
    };

    auto sync_all = [&]() {
        for (int i = 0; i < NRANKS; i++) {
            CHK_CUDA(cudaSetDevice(i));
            CHK_CUDA(cudaStreamSynchronize(streams[i]));
        }
    };

    for (int it = 0; it < warmup; it++) run();
    sync_all();

    auto t0 = std::chrono::steady_clock::now();
    for (int it = 0; it < iters; it++) run();
    sync_all();
    auto t1 = std::chrono::steady_clock::now();

    const double sec = std::chrono::duration<double>(t1 - t0).count() / iters;
    const double per_link_unidir = bytes / sec / 1e9;
    const double per_link_bidir  = 2.0 * bytes / sec / 1e9;

    printf("mode=%s bytes=%zu iters=%d time/iter=%.3f ms\n",
           mode_name(mode), bytes, iters, sec * 1e3);
    printf("per-link unidirectional: %6.2f GB/s\n", per_link_unidir);
    if (mode != Mode::Unidir)
        printf("per-link bidirectional:  %6.2f GB/s\n", per_link_bidir);

    for (int i = 0; i < NRANKS; i++) {
        cudaSetDevice(i);
        cudaFree(sn[i]); cudaFree(rp[i]);
        if (ring_bi) { cudaFree(sp[i]); cudaFree(rn[i]); }
        cudaStreamDestroy(streams[i]);
        ncclCommDestroy(comms[i]);
    }
    return 0;
}
