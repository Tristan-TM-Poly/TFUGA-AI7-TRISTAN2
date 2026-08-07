#include <cstdint>

extern "C" std::uint64_t omega_dot_u64_cpp(const std::uint64_t *a,
                                             const std::uint64_t *b,
                                             std::uint64_t n) {
    std::uint64_t acc = 0;
    for (std::uint64_t i = 0; i < n; ++i) {
        acc += a[i] * b[i];
    }
    return acc;
}
