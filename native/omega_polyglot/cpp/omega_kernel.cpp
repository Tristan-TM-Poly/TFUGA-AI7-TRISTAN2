#include <cstddef>

extern "C" int omega_vector_affine_f64(
    const double *__restrict x,
    const double *__restrict y,
    double scalar,
    double *__restrict output,
    std::size_t length
) noexcept {
    if (length > 0 && (x == nullptr || y == nullptr || output == nullptr)) {
        return 1;
    }
    for (std::size_t index = 0; index < length; ++index) {
        output[index] = scalar * x[index] + y[index];
    }
    return 0;
}
