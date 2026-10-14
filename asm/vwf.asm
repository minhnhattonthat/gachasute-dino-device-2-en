; Variable-width font for the dialogue printer (0x0800D210) and the menu printer's glyph call (0x0800BE60).
; Assembled by build.py: armips asm/vwf.asm -strequ ROM <rom> -definelabel CodeBase <addr>
;                        -definelabel VwfFont <addr> -definelabel VwfWidths <addr>
; Font: 1 bit per pixel, bit set = ink, MSB = left column, 8 bytes per glyph; VwfWidths: 1 byte per glyph.
; Each glyph's width includes its trailing blank column, so the shadow pixel stays inside the glyph.
; State: the partially filled tile lives in a 2-tile 4bpp buffer. A draw continues it only if the game's own
; position counters still equal what the last draw left behind; a newline, page or new string changes them.
.gba
.open ROM, 0x08000000

T           equ 0x0200471C      ; dialogue interpreter state
DLG         equ 0x0203FF00      ; dialogue VWF state
MENU        equ 0x0203FF80      ; menu VWF state
; state layout
S_AFTER     equ 0x00            ; dialogue: map index the game should be at; menu: map entry pointer
S_AFTERT    equ 0x04            ; tile index the game should be at
S_SHIFT     equ 0x08            ; pixels used in the current tile (0-7)
S_CUR       equ 0x0C            ; current cell: dialogue map index / menu map entry pointer
S_CURT      equ 0x10            ; current tile index
S_MONO      equ 0x14            ; menu only: [mono] active
S_MONOMAP   equ 0x18            ; menu only: map entry pointer the next mono glyph must arrive with
S_MONOTILE  equ 0x1C            ; menu only: tile index the next mono glyph must arrive with
S_NARROW    equ 0x60            ; menu only: [narrow] active (condensed font) until the next fresh string
S_BUF       equ 0x20            ; 64 bytes: current tile, next tile

.org 0x0800D210
.thumb
    ldr r3, [pc, #0]
    bx r3
.word VwfDialog | 1

.org 0x0800BE60
.thumb
    ldr r3, [pc, #0]
    bx r3
.word VwfMenu | 1

.org CodeBase
.thumb
.align 4

; ---------------------------------------------------------------------------------------------------------
; VwfDialog: replaces 0x0800D210 (draw glyph [T+0x1C] at map index [T+0x30], tile [T+0x34]).
; Window config W = [T+0x8C]: +0x0E first tile, +0x10 last tile, +0x16 palette, +0x17 fg, +0x18 bg, +0x19 shadow.
; Glyph 0x100-0x11F = tab: continue at cell (glyph & 0x1F) of the current line ([T+0x20] = line start).
VwfDialog:
    push {r4-r7, lr}
    mov r3, r8
    push {r3}
    ldr r4, =T
    ldr r7, =DLG
    ldr r0, [r4, #0x1C]
    lsr r1, r0, #8
    beq @@glyph
    sub r0, #0xFF
    sub r0, #1                 ; glyph - 0x100
    cmp r0, #0x20
    bhs @@done                  ; other extended glyphs: ignored
    ldr r1, [r4, #0x20]
    add r1, r1, r0
    str r1, [r4, #0x30]
    mov r0, #0
    mvn r0, r0
    str r0, [r7, #S_AFTER]      ; force a fresh tile on the next glyph
    b @@done
@@glyph:
    mov r0, r4
    add r0, #0x8C
    ldr r5, [r0]                ; W
    ; colours: fg = [T+0x7E] or W+0x17; bg = W+0x18; shadow = W+0x19 or bg
    mov r0, r4
    add r0, #0x7E
    ldrb r2, [r0]
    cmp r2, #0
    bne @@fg
    ldrb r2, [r5, #0x17]
@@fg:
    ldrb r1, [r5, #0x18]
    lsl r0, r1, #8
    orr r2, r0
    ldrb r0, [r5, #0x19]
    cmp r0, #0
    bne @@sh
    mov r0, r1
@@sh:
    lsl r0, r0, #16
    orr r2, r0
    mov r8, r2                  ; r8 = colours
    ; fresh tile unless counters match what we left
    ldr r0, [r4, #0x30]
    ldr r1, [r4, #0x34]
    ldr r2, [r7, #S_AFTER]
    cmp r0, r2
    bne @@fresh
    ldr r2, [r7, #S_AFTERT]
    cmp r1, r2
    beq @@draw
@@fresh:
    str r0, [r7, #S_CUR]
    str r1, [r7, #S_CURT]
    mov r0, #0
    str r0, [r7, #S_SHIFT]
    mov r0, r7
    mov r1, r8
    bl VwfClear
@@draw:
    mov r0, r7
    ldr r1, [r4, #0x1C]
    mov r2, r8
    bl VwfRender                ; r0 = new shift
    mov r6, r0
    ; upload current tile, map entry
    ldr r0, [r7, #S_CURT]
    bl @@put_tile0
    ldr r0, [r7, #S_CUR]
    ldr r1, [r7, #S_CURT]
    bl @@put_map
    cmp r6, #8
    bls @@no_spill
    ldr r0, [r7, #S_CURT]
    bl @@next_tile
    push {r0}
    mov r1, r7
    add r1, #S_BUF + 0x20
    bl @@put_tile
    ldr r0, [r7, #S_CUR]
    add r0, #1
    pop {r1}
    bl @@put_map
@@no_spill:
    cmp r6, #8
    blo @@report
    ; current tile is full: move on
    sub r6, #8
    ldr r0, [r7, #S_CUR]
    add r0, #1
    str r0, [r7, #S_CUR]
    ldr r0, [r7, #S_CURT]
    bl @@next_tile
    str r0, [r7, #S_CURT]
    mov r0, r7
    mov r1, r8
    bl VwfShiftBuf
@@report:
    str r6, [r7, #S_SHIFT]
    ldr r0, [r7, #S_CUR]
    ldr r1, [r7, #S_CURT]
    cmp r6, #0
    beq @@rep
    add r0, #1
    push {r0}
    mov r0, r1
    bl @@next_tile
    mov r1, r0
    pop {r0}
@@rep:
    str r0, [r4, #0x30]
    str r1, [r4, #0x34]
    str r0, [r7, #S_AFTER]
    str r1, [r7, #S_AFTERT]
@@done:
    pop {r3}
    mov r8, r3
    pop {r4-r7}
    pop {r0}
    bx r0

; r0 = tile index -> next tile index with the window's wrap (W+0x10 last, W+0x0E first). Uses r5 = W.
@@next_tile:
    add r0, #1
    ldrh r1, [r5, #0x10]
    cmp r0, r1
    bls @@nt_ok
    ldrh r0, [r5, #0x0E]
@@nt_ok:
    bx lr

; r0 = tile index: copy buffer tile 0 to VRAM [T+0x0C] + index*32
@@put_tile0:
    mov r1, r7
    add r1, #S_BUF
; r0 = tile index, r1 = source (32 bytes)
@@put_tile:
    lsl r0, r0, #5
    ldr r2, [r4, #0x0C]
    add r0, r0, r2
    ldmia r1!, {r2, r3}
    stmia r0!, {r2, r3}
    ldmia r1!, {r2, r3}
    stmia r0!, {r2, r3}
    ldmia r1!, {r2, r3}
    stmia r0!, {r2, r3}
    ldmia r1!, {r2, r3}
    stmia r0!, {r2, r3}
    bx lr

; r0 = map index, r1 = tile index: map[T+0x10][index] = W+0x16 << 12 | tile
@@put_map:
    lsl r0, r0, #1
    ldr r2, [r4, #0x10]
    add r0, r0, r2
    ldrb r2, [r5, #0x16]
    lsl r2, r2, #12
    orr r1, r2
    strh r1, [r0]
    bx lr
.pool

; ---------------------------------------------------------------------------------------------------------
; VwfMenu: replaces 0x0800BE60(r0 = glyph, r1 = S). S: +0 map entry pointer, +4 VRAM tile base,
; +0x0C tile index (u16), +0x0E palette, +0x0F fg, +0x10 bg, +0x11 shadow.
; The caller adds 2 to S+0 and 1 to S+0x0C after each glyph, so we leave them one cell behind what we want.
VwfMenu:
    push {r4-r7, lr}
    mov r3, r8
    push {r3}
    mov r4, r1                  ; S
    ldr r7, =MENU
    mov r6, r0                  ; glyph
    ; glyph 0x120 = [mono]: the rest of this string is drawn one glyph per cell with the original renderer
    ; (font strips such as the digit tiles other screens point their maps at)
    ldr r1, =0x120
    cmp r0, r1
    bne @@not_mono_tag
    mov r0, #1
    str r0, [r7, #S_MONO]
    ldr r0, [r4, #0]
    str r0, [r7, #S_MONOMAP]
    ldrh r0, [r4, #0x0C]
    str r0, [r7, #S_MONOTILE]
    b @@skip
@@not_mono_tag:
    ldr r0, [r7, #S_MONO]
    cmp r0, #0
    beq @@vwf
    ldr r0, [r4, #0]
    ldr r1, [r7, #S_MONOMAP]
    cmp r0, r1
    bne @@mono_off
    ldrh r0, [r4, #0x0C]
    ldr r1, [r7, #S_MONOTILE]
    cmp r0, r1
    bne @@mono_off
    bl @@mono_draw
    ldr r0, [r4, #0]
    add r0, #2
    str r0, [r7, #S_MONOMAP]
    ldrh r0, [r4, #0x0C]
    add r0, #1
    str r0, [r7, #S_MONOTILE]
    b @@done
@@mono_off:
    mov r0, #0
    str r0, [r7, #S_MONO]
@@vwf:
    ; glyph 0x121 = [narrow]: condensed font for the rest of this string. Start the string here (fresh tile)
    ; and make the next glyph arrive as a continuation so the fresh path (which clears the flag) is skipped.
    ldr r1, =0x121
    cmp r6, r1
    bne @@not_narrow_tag
    mov r0, #1
    str r0, [r7, #S_NARROW]
    ldr r0, [r4, #0]
    str r0, [r7, #S_AFTER]
    str r0, [r7, #S_CUR]
    ldrh r1, [r4, #0x0C]
    str r1, [r7, #S_AFTERT]
    str r1, [r7, #S_CURT]
    mov r0, #0
    str r0, [r7, #S_SHIFT]
    ldrb r1, [r4, #0x10]        ; bg colour for the clear
    lsl r1, r1, #8
    mov r0, r7
    bl VwfClear
    b @@skip
@@not_narrow_tag:
    mov r0, r6
    cmp r0, #0xFF
    bhi @@skip                  ; tabs/extended glyphs: not in menus
    ; colours
    ldrb r2, [r4, #0x0F]
    ldrb r1, [r4, #0x10]
    lsl r0, r1, #8
    orr r2, r0
    ldrb r0, [r4, #0x11]
    cmp r0, #0
    bne @@sh
    mov r0, r1
@@sh:
    lsl r0, r0, #16
    orr r2, r0
    mov r8, r2
    ldr r0, [r4, #0]
    ldrh r1, [r4, #0x0C]
    ldr r2, [r7, #S_AFTER]
    cmp r0, r2
    bne @@fresh
    ldr r2, [r7, #S_AFTERT]
    cmp r1, r2
    beq @@draw
@@fresh:
    str r0, [r7, #S_CUR]
    str r1, [r7, #S_CURT]
    mov r0, #0
    str r0, [r7, #S_SHIFT]
    str r0, [r7, #S_NARROW]     ; a new string starts in the normal font
    mov r0, r7
    mov r1, r8
    bl VwfClear
@@draw:
    mov r0, r7
    mov r1, r6
    mov r2, r8
    bl VwfRender
    mov r6, r0
    ldr r0, [r7, #S_CURT]
    mov r1, r7
    add r1, #S_BUF
    bl @@put_tile
    ldr r0, [r7, #S_CUR]
    ldr r1, [r7, #S_CURT]
    bl @@put_map
    cmp r6, #8
    bls @@no_spill
    ldr r0, [r7, #S_CURT]
    add r0, #1
    mov r1, r7
    add r1, #S_BUF + 0x20
    bl @@put_tile
    ldr r0, [r7, #S_CUR]
    add r0, #2
    ldr r1, [r7, #S_CURT]
    add r1, #1
    bl @@put_map
@@no_spill:
    cmp r6, #8
    blo @@report
    sub r6, #8
    ldr r0, [r7, #S_CUR]
    add r0, #2
    str r0, [r7, #S_CUR]
    ldr r0, [r7, #S_CURT]
    add r0, #1
    str r0, [r7, #S_CURT]
    mov r0, r7
    mov r1, r8
    bl VwfShiftBuf
@@report:
    str r6, [r7, #S_SHIFT]
    ldr r0, [r7, #S_CUR]
    ldr r1, [r7, #S_CURT]
    cmp r6, #0
    beq @@rep
    add r0, #2
    add r1, #1
@@rep:
    str r0, [r7, #S_AFTER]
    str r1, [r7, #S_AFTERT]
    sub r0, #2                 ; caller adds these back
    sub r1, #1
    str r0, [r4, #0]
    strh r1, [r4, #0x0C]
    b @@done
@@skip:
    ldr r0, [r4, #0]            ; occupy no cell
    sub r0, #2
    str r0, [r4, #0]
    ldrh r1, [r4, #0x0C]
    sub r1, #1
    strh r1, [r4, #0x0C]
@@done:
    pop {r3}
    mov r8, r3
    pop {r4-r7}
    pop {r0}
    bx r0

; r0 = tile index, r1 = source: copy 32 bytes to VRAM S+4 + index*32
@@put_tile:
    lsl r0, r0, #5
    ldr r2, [r4, #4]
    add r0, r0, r2
    ldmia r1!, {r2, r3}
    stmia r0!, {r2, r3}
    ldmia r1!, {r2, r3}
    stmia r0!, {r2, r3}
    ldmia r1!, {r2, r3}
    stmia r0!, {r2, r3}
    ldmia r1!, {r2, r3}
    stmia r0!, {r2, r3}
    bx lr

; r0 = map entry pointer, r1 = tile index
@@put_map:
    ldrb r2, [r4, #0x0E]
    lsl r2, r2, #12
    orr r1, r2
    strh r1, [r0]
    bx lr

; original fixed-cell draw of glyph r6 at S's map entry/tile (what 0x0800BE60 did)
@@mono_draw:
    push {lr}
    sub sp, #0x24
    add r0, sp, #4
    str r0, [sp]                ; 0x0800BD70 takes the destination buffer as its stack argument
    mov r0, r6
    ldrb r1, [r4, #0x0F]
    ldrb r2, [r4, #0x10]
    ldrb r3, [r4, #0x11]
    bl @@call_bd70
    ldrh r0, [r4, #0x0C]
    add r1, sp, #4
    bl @@put_tile
    ldr r0, [r4, #0]
    ldrh r1, [r4, #0x0C]
    bl @@put_map
    add sp, #0x24
    pop {r0}
    bx r0
@@call_bd70:
    push {r7}
    ldr r7, =0x0800BD71
    mov r12, r7
    pop {r7}
    bx r12
.pool

; ---------------------------------------------------------------------------------------------------------
; VwfClear(r0 = state, r1 = colours): fill both buffer tiles with the background colour.
VwfClear:
    lsr r1, r1, #8
    mov r2, #0xF
    and r1, r2
    lsl r2, r1, #4
    orr r1, r2                 ; bg byte
    lsl r2, r1, #8
    orr r1, r2
    lsl r2, r1, #16
    orr r1, r2                 ; bg word
    add r0, #S_BUF
    mov r2, #16
@@loop:
    stmia r0!, {r1}
    sub r2, #1
    bne @@loop
    bx lr

; VwfShiftBuf(r0 = state, r1 = colours): tile 1 -> tile 0, tile 1 = background.
VwfShiftBuf:
    push {r0, r4}
    add r0, #S_BUF
    mov r2, r0
    add r2, #0x20
    mov r3, #8
@@loop:
    ldmia r2!, {r4}
    stmia r0!, {r4}
    sub r3, #1
    bne @@loop
    pop {r0, r4}
    b VwfClearTile1

; fill tile 1 only: r0 = state, r1 = colours
VwfClearTile1:
    lsr r1, r1, #8
    mov r2, #0xF
    and r1, r2
    lsl r2, r1, #4
    orr r1, r2
    lsl r2, r1, #8
    orr r1, r2
    lsl r2, r1, #16
    orr r1, r2
    add r0, #S_BUF + 0x20
    mov r2, #8
@@loop:
    stmia r0!, {r1}
    sub r2, #1
    bne @@loop
    bx lr

; ---------------------------------------------------------------------------------------------------------
; VwfRender(r0 = state, r1 = glyph 0-255, r2 = colours fg | bg << 8 | shadow << 16) -> r0 = shift + width.
; Ink -> fg; blank right after ink -> shadow; other blank -> bg (same rule as the original 0x0800BD70).
VwfRender:
    push {r4-r7, lr}
    mov r3, r8
    push {r3}
    ldr r3, [r0, #S_SHIFT]
    mov r8, r3                  ; r8 = shift
    ldr r3, =VwfWidths
    ldr r4, =VwfFont
    ldr r5, [r0, #S_NARROW]     ; 0 for the dialogue state (never set there)
    cmp r5, #0
    beq @@normal
    ldr r3, =NarrowWidths
    ldr r4, =NarrowFont
@@normal:
    ldrb r3, [r3, r1]           ; r3 = width
    lsl r1, r1, #3
    add r1, r1, r4             ; r1 = glyph rows
    add r0, #S_BUF             ; r0 = buffer
    mov r4, #0                 ; y
@@row:
    mov r5, #0                 ; x
    cmp r3, #0
    beq @@next_row
@@pix:
    ldrb r6, [r1, r4]
    lsl r6, r5                 ; bit 0x80 = column x, 0x100 = column x-1
    mov r7, #0x80
    tst r6, r7
    bne @@ink
    lsl r7, r7, #1
    tst r6, r7
    bne @@shadow
    lsr r7, r2, #8
    b @@colour
@@ink:
    mov r7, r2
    b @@colour
@@shadow:
    lsr r7, r2, #16
@@colour:
    mov r6, #0xF
    and r7, r6                 ; r7 = colour
    mov r6, r8
    add r6, r6, r5             ; X = shift + x (0-15)
    push {r1, r2}
    lsr r1, r6, #3
    lsl r1, r1, #5             ; tile * 32
    lsl r2, r4, #2
    add r1, r1, r2             ; + y * 4
    lsl r2, r6, #29
    lsr r2, r2, #30            ; + (X & 7) >> 1
    add r1, r1, r2
    add r1, r1, r0
    ldrb r2, [r1]
    lsl r6, r6, #31
    bne @@odd
    mov r6, #0xF0
    and r2, r6
    orr r2, r7
    b @@store
@@odd:
    mov r6, #0x0F
    and r2, r6
    lsl r7, r7, #4
    orr r2, r7
@@store:
    strb r2, [r1]
    pop {r1, r2}
    add r5, #1
    cmp r5, r3
    blo @@pix
@@next_row:
    add r4, #1
    cmp r4, #8
    blo @@row
    mov r0, r8
    add r0, r0, r3
    pop {r3}
    mov r8, r3
    pop {r4-r7}
    pop {r1}
    bx r1
.pool

.close
