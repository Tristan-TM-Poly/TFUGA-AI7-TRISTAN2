use std::slice;

#[no_mangle]
pub unsafe extern "C" fn omega_vector_affine_f64(
    x: *const f64,
    y: *const f64,
    scalar: f64,
    output: *mut f64,
    length: usize,
) -> i32 {
    if length > 0 && (x.is_null() || y.is_null() || output.is_null()) {
        return 1;
    }

    let x_values = slice::from_raw_parts(x, length);
    let y_values = slice::from_raw_parts(y, length);
    let output_values = slice::from_raw_parts_mut(output, length);

    for index in 0..length {
        output_values[index] = scalar * x_values[index] + y_values[index];
    }
    0
}
