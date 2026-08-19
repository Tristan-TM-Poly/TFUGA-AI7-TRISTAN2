const MOD: u64 = 998_244_353;
const ROOT: u64 = 3;

fn mul_mod(a: u64, b: u64, modulus: u64) -> u64 {
    ((a as u128 * b as u128) % modulus as u128) as u64
}

fn pow_mod(mut base: u64, mut exp: u64, modulus: u64) -> u64 {
    let mut result = 1 % modulus;
    base %= modulus;
    while exp > 0 {
        if exp & 1 == 1 { result = mul_mod(result, base, modulus); }
        base = mul_mod(base, base, modulus);
        exp >>= 1;
    }
    result
}

fn sprp(n: u64, a: u64) -> bool {
    if a % n == 0 { return true; }
    let mut d = n - 1;
    let mut s = 0;
    while d & 1 == 0 { d >>= 1; s += 1; }
    let mut x = pow_mod(a, d, n);
    if x == 1 || x == n - 1 { return true; }
    for _ in 1..s {
        x = mul_mod(x, x, n);
        if x == n - 1 { return true; }
    }
    false
}

fn is_prime(n: u64) -> bool {
    if n < 2 { return false; }
    for p in [2,3,5,7,11,13,17,19,23,29,31,37] {
        if n == p { return true; }
        if n % p == 0 { return false; }
    }
    for a in [2,325,9375,28178,450775,9780504,1795265022] {
        if !sprp(n, a) { return false; }
    }
    true
}

fn ntt(mut a: Vec<u64>, invert: bool) -> Vec<u64> {
    let n = a.len();
    let mut j = 0usize;
    for i in 1..n {
        let mut bit = n >> 1;
        while j & bit != 0 { j ^= bit; bit >>= 1; }
        j ^= bit;
        if i < j { a.swap(i, j); }
    }
    let mut len = 2usize;
    while len <= n {
        let mut wlen = pow_mod(ROOT, (MOD - 1) / len as u64, MOD);
        if invert { wlen = pow_mod(wlen, MOD - 2, MOD); }
        for i in (0..n).step_by(len) {
            let mut w = 1u64;
            for j in 0..len/2 {
                let u = a[i+j];
                let v = mul_mod(a[i+j+len/2], w, MOD);
                a[i+j] = (u + v) % MOD;
                a[i+j+len/2] = (u + MOD - v) % MOD;
                w = mul_mod(w, wlen, MOD);
            }
        }
        len <<= 1;
    }
    if invert {
        let inv_n = pow_mod(n as u64, MOD - 2, MOD);
        for x in &mut a { *x = mul_mod(*x, inv_n, MOD); }
    }
    a
}

fn convolution(left: &[u64], right: &[u64]) -> Vec<u64> {
    let needed = left.len() + right.len() - 1;
    let mut n = 1usize;
    while n < needed { n <<= 1; }
    let mut a = vec![0u64; n];
    let mut b = vec![0u64; n];
    a[..left.len()].copy_from_slice(left);
    b[..right.len()].copy_from_slice(right);
    a = ntt(a, false);
    b = ntt(b, false);
    for i in 0..n { a[i] = mul_mod(a[i], b[i], MOD); }
    a = ntt(a, true);
    a.truncate(needed);
    a
}

fn main() {
    let values: [u64; 14] = [
        2,3,5,17,97,998244353,18446744073709551557,
        0,1,4,9,341,561,18446744073709551615
    ];
    let conv = convolution(&[1,2,3,4,5], &[7,11,13]);
    print!("{{\"convolution\":[");
    for (i, value) in conv.iter().enumerate() {
        if i > 0 { print!(","); }
        print!("{}", value);
    }
    print!("],\"mod_pow\":{},\"primality\":{{", pow_mod(123456789, 12345, MOD));
    for (i, value) in values.iter().enumerate() {
        if i > 0 { print!(","); }
        print!("\"{}\":{}", value, if is_prime(*value) { "true" } else { "false" });
    }
    println!("}}}}");
}
