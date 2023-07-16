; This is a comment
@ This is also a comment

mov r1,#0
ldr r2,[r2]
mov r3,#0
ldr r4,[r4]
sub r4,r4,#1
mov r5,#0
mov r6,#0

SEARCH: cmp r3,r4
bgt NOTFOUND

sub r6,r4,#1
add r5,r3,r6,LSR#1
ldr r1,[r0,r5,LSL#2]
cmp r1,r2
beq FOUND
blt L1

sub r4,r5,#1
b SEARCH

L1: add r3,r5,#1
b SEARCH

FOUND: mov r10,#1
swi 0x011

NOTFOUND: mov r10,#-1
swi 0x011
