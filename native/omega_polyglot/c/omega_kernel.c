#include <stddef.h>

int omega_vector_affine_f64(
    const double *x,
    const double *y,
    double scalar,
    double *output,
    size_t length
) {
    if (length > 0 && (x == NULL || y == NULL || output == NULL)) {
        return 1;
    }
    for (size_t index = 0; index < length; ++index) {
        output[index] = scalar * x[index] + y[index];
    }
    return 0;
}
