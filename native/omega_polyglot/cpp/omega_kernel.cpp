#include <cstddef>

extern "C" int omega_vector_affine_f64(
    const double *x,
    const double *y,
    double scalar,
    double *output,
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
