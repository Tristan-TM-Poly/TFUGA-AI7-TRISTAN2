.text
.globl omega_dot_u64_indexed
.type omega_dot_u64_indexed,@function
omega_dot_u64_indexed:
    xorq %rax, %rax
    xorq %rcx, %rcx
.Lomega_dot_u64_indexed_loop:
    cmpq %rdx, %rcx
    jae .Lomega_dot_u64_indexed_done
    movq (%rdi,%rcx,8), %r8
    imulq (%rsi,%rcx,8), %r8
    addq %r8, %rax
    incq %rcx
    jmp .Lomega_dot_u64_indexed_loop
.Lomega_dot_u64_indexed_done:
    ret
.size omega_dot_u64_indexed, .-omega_dot_u64_indexed

.globl omega_dot_u64_ptr
.type omega_dot_u64_ptr,@function
omega_dot_u64_ptr:
    xorq %rax, %rax
    testq %rdx, %rdx
    je .Lomega_dot_u64_ptr_done
.Lomega_dot_u64_ptr_loop:
    movq (%rdi), %r8
    imulq (%rsi), %r8
    addq %r8, %rax
    addq $8, %rdi
    addq $8, %rsi
    decq %rdx
    jne .Lomega_dot_u64_ptr_loop
.Lomega_dot_u64_ptr_done:
    ret
.size omega_dot_u64_ptr, .-omega_dot_u64_ptr

.section .note.GNU-stack,"",@progbits
