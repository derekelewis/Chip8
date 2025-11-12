; Prime sieve + on-screen visualization
; Flags at #300 (1=prime, 0=composite). Primes drawn as 4x2 blocks on a 16x16 grid.

define SIEVE_BASE #300

offset #200

start:
    CLS

    ; ---------------------------
    ; Init A[0..255] = 1
    ; ---------------------------
    LD  V0, #01
    LD  V5, #00            ; i = 0

init_loop:
    LD  I, SIEVE_BASE
    ADD I, V5
    LD  [I], V0            ; A[i] = 1
    ADD V5, #01            ; i++
    SE  V5, #00            ; when wrapped to 0 (after 255), done
    JP  init_loop

    ; A[0] = A[1] = 0
    LD  V0, #00
    LD  V5, #00
    LD  I, SIEVE_BASE
    ADD I, V5
    LD  [I], V0

    LD  V5, #01
    LD  I, SIEVE_BASE
    ADD I, V5
    LD  [I], V0

    ; ---------------------------
    ; Sieve: for p = 2..15
    ; ---------------------------
    LD  V1, #02            ; p = 2

outer_loop:
    SNE V1, #10            ; if p == 16 -> render (since 16^2 > 255)
    JP  render

    ; if A[p] != 1, skip marking
    LD  I, SIEVE_BASE
    ADD I, V1
    LD  V0, [I]            ; V0 = A[p]
    SE  V0, #01            ; if A[p] == 1 skip next JP
    JP  next_p

    ; mark multiples: m = 2p, 3p, ...
    LD  V2, V1
    ADD V2, V1             ; m = 2p

mark_loop:
    LD  V0, #00
    LD  I, SIEVE_BASE
    ADD I, V2
    LD  [I], V0            ; A[m] = 0
    ADD V2, V1             ; m += p  (VF=carry on overflow)
    SE  VF, #01            ; if overflow, stop
    JP  mark_loop

next_p:
    ADD V1, #01            ; p++
    JP  outer_loop

; ---------------------------
; Render primes to screen
;  - Grid: 16x16 => numbers 0..255
;  - Each prime = 4x2 block
; ---------------------------
render:
    LD  V6, #00            ; n = 0..255
    LD  V7, #0F            ; mask for low nibble

render_loop:
    ; read A[n]
    LD  I, SIEVE_BASE
    ADD I, V6
    LD  V0, [I]            ; V0 = A[n]
    SE  V0, #01            ; if prime, skip JP and draw
    JP  next_n

    ; x = (n & 0xF) * 4
    LD  V3, V6
    AND V3, V7
    ADD V3, V3             ; *2
    ADD V3, V3             ; *4

    ; y = (n >> 4) * 2
    LD  V4, V6
    SHR V4                 ; /2
    SHR V4                 ; /4
    SHR V4                 ; /8
    SHR V4                 ; /16  => row
    ADD V4, V4             ; *2   => 2-pixel tall

    ; draw 4x2 block sprite at (V3,V4)
    LD  I, pix4x2
    DRW V3, V4, #2

next_n:
    ADD V6, #01
    SE  V6, #00            ; loop until wrap after 255
    JP  render_loop

halt:
    JP  halt               ; stop here

; 4x2 filled block sprite (11110000 over two rows)
pix4x2:
    db #F0, #F0

