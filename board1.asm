; ==============================================================================
; UNIVERSITY: ESOGU - Electrical & Electronics / Computer Engineering
; COURSE:     Introduction to Microcomputers - Term Project
; FILE:       board2.asm (Board #2 - Curtain Control System)
; DATE:       January 2026
;
; AUTHORS:
; 1. Yusuf Yaman - 152120221075
; 2. An?l
;
; DESCRIPTION:
; This code controls the Curtain System (Board #2).
; It manages the Step Motor, LDR Sensor, Potentiometer, and LCD Display.
; It communicates with the PC using UART protocol.
; ==============================================================================

LIST P=16F877A
    INCLUDE "P16F877A.INC"

    ; Config: No Watchdog, 4MHz Crystal Oscillator, Brown-out Reset ON
    __CONFIG _CP_OFF & _WDT_OFF & _BODEN_ON & _PWRTE_ON & _XT_OSC & _WRT_OFF & _LVP_OFF & _CPD_OFF

; --- PIN DEFINITIONS ---
#define RS PORTB, 4         ; LCD Register Select pin
#define EN PORTB, 5         ; LCD Enable pin
#define SW_MAN PORTA, 2     ; Switch for Auto/Manual Mode

; --- VARIABLES (Memory) ---
    CBLOCK 0x20
        SAYAC1, SAYAC2      ; Counters for delay loops
        
        ; [R2.2.1-1] Stores the target curtain position (0-63)
        DESIRED_ST
        
        ; [R2.2.1-2] Stores the current curtain position (0-63)
        CURRENT_ST
        
        ; Variables to separate digits for LCD (Hundreds, Tens, Ones)
        BIN_H, BIN_L, YUZ_H, ON_H, BIR_H
        
        ; [R2.2.2-1] Stores the Light Intensity value (from LDR)
        LDR_VAL
        
        ; Stores the Potentiometer value (for Manual Mode)
        POT_VAL
        
        TEMP_MATH           ; Temp variable for math operations
        LAST_DISP_ST        ; Last curtain value shown on LCD (to avoid flickering)
        LAST_LDR            ; Last LDR value shown on LCD
        PHASE_STEP          ; Step motor phase index (0-3)
        SYSTEM_MODE         ; 0=Auto, 1=Manual, 2=PC Control
        UART_TEMP           ; Temp variable for UART data
        UART_LOW_BYTE       ; Temp variable for low byte of commands
    ENDC

    ORG 0x00
    GOTO SETUP

; ==============================================================================
; SETUP: Initialize Ports and Modules
; ==============================================================================
SETUP
    ; Switch to Bank 1 to set inputs/outputs
    BSF     STATUS, RP0
    
    CLRF    TRISD           ; Make PORTD Output (for LCD Data)
    MOVLW   B'11000000'     
    MOVWF   TRISB           ; PORTB: RB6, RB7 Input (Debug), others Output
    MOVLW   B'00000111'
    MOVWF   TRISA           ; PORTA: RA0, RA1, RA2 are Inputs (Sensors)
    
    ; --- UART Setup [R2.2.6-1] ---
    BCF     TRISC, 6        ; TX is Output
    BSF     TRISC, 7        ; RX is Input
    MOVLW   D'25'           ; Set Baud Rate to 9600 (for 4MHz clock)
    MOVWF   SPBRG
    MOVLW   B'00100100'     ; Enable Transmission (TX), High Speed mode
    MOVWF   TXSTA
    
    ; --- ADC Setup ---
    MOVLW   B'00000100'     ; Configure AN0 and AN1 as Analog Inputs
    MOVWF   ADCON1
    
    ; Switch back to Bank 0
    BCF     STATUS, RP0
    
    MOVLW   B'10010000'     ; Enable Serial Port (SPEN) and Receiver (CREN)
    MOVWF   RCSTA
    
    MOVLW   B'10000001'     ; Turn on ADC module
    MOVWF   ADCON0
    
    ; Clear variables at startup
    CLRF    SYSTEM_MODE
    CLRF    PHASE_STEP
    CLRF    UART_LOW_BYTE
    
    ; Set initial values
    MOVLW   D'32'           ; Start with 50% curtain open
    MOVWF   DESIRED_ST
    MOVWF   CURRENT_ST      ; Assume motor is at the target
    
    MOVLW   0xFF
    MOVWF   LAST_DISP_ST    ; Force LCD update in the first loop
    
    ; --- UART FLUSH ---
    ; Clear any garbage data in the buffer to prevent errors
    MOVF    RCREG, W
    MOVF    RCREG, W
    MOVF    RCREG, W
    
    ; Initialize LCD
    CALL    LCD_INIT
    CALL    EKRAN_SABLON    ; Write static text (MOD, L, C) on screen
    
    GOTO    ANA_DONGU

; ==============================================================================
; MAIN LOOP
; ==============================================================================
ANA_DONGU
    CALL    UART_DINLE_VE_ISLE  ; Check commands from PC [R2.2.6-1]
    CALL    SENSORLERI_OKU      ; Read LDR and Potentiometer
    
    ; Check which mode we are in
    MOVF    SYSTEM_MODE, W
    SUBLW   D'2'
    BTFSC   STATUS, Z           ; If SYSTEM_MODE == 2, go to PC loop
    GOTO    ISLEM_PC
    
    ; Check the hardware switch
    BTFSC   SW_MAN              ; If Switch is 1, go to Manual Mode
    GOTO    ISLEM_MANUEL
    GOTO    ISLEM_AUTO          ; Else, go to Auto Mode

; ------------------------------------------------------------------------------
; MANUEL MODE [R2.2.4-1]
; Control curtain using the Potentiometer.
; ------------------------------------------------------------------------------
ISLEM_MANUEL
    MOVLW   D'1'
    MOVWF   SYSTEM_MODE     ; Set mode to Manual
    
    ; Convert Pot value (0-255) to Curtain value (0-63)
    ; We divide by 4 (Shift Right 2 times)
    MOVF    POT_VAL, W
    MOVWF   TEMP_MATH
    BCF     STATUS, C
    RRF     TEMP_MATH, F    ; Divide by 2
    BCF     STATUS, C
    RRF     TEMP_MATH, W    ; Divide by 4
    
    MOVWF   DESIRED_ST      ; Set new target [R2.2.1-1]
    CALL    LIMIT_63        ; Make sure it is not > 63
    GOTO    UYGULA

; ------------------------------------------------------------------------------
; AUTO MODE [R2.2.2-2]
; Control curtain based on Light Intensity (LDR).
; ------------------------------------------------------------------------------
ISLEM_AUTO
    MOVLW   D'0'
    MOVWF   SYSTEM_MODE     ; Set mode to Auto
    
    ; Check if it is dark (LDR < 100)
    MOVLW   D'100'
    SUBWF   LDR_VAL, W
    BTFSS   STATUS, C       ; If LDR < 100 (Carry is 0)
    GOTO    AUTO_KARANLIK
    
    CLRF    DESIRED_ST      ; Light -> Open Curtain (0%)
    GOTO    UYGULA
    
AUTO_KARANLIK
    MOVLW   D'63'           ; Dark -> Close Curtain (100% -> 63)
    MOVWF   DESIRED_ST

; --- Apply Changes ---
UYGULA
    CALL    MOTOR_HAREKET   ; Move the motor if needed
    CALL    EKRANI_GUNCELLE ; Update the LCD [R2.2.5-1]
    GOTO    ANA_DONGU

; --- PC Mode Loop ---
ISLEM_PC
    CALL    MOTOR_HAREKET   ; Only move motor and update screen
    CALL    EKRANI_GUNCELLE ; Values are set by UART commands
    GOTO    ANA_DONGU

; Limit value to max 63
LIMIT_63
    MOVLW   D'63'
    SUBWF   DESIRED_ST, W
    BTFSC   STATUS, C       ; If DESIRED_ST > 63
    GOTO    SET_MAX_63
    RETURN
SET_MAX_63
    MOVLW   D'63'
    MOVWF   DESIRED_ST
    RETURN

; ==============================================================================
; SENSOR READING [R2.2.2-1], [R2.2.4-1]
; Uses "Double Read" method to fix stability issues.
; ==============================================================================
SENSORLERI_OKU
    ; --- Read LDR (Channel 0) ---
    BCF     STATUS, RP0
    MOVLW   B'10000001'     ; Select AN0 (LDR)
    MOVWF   ADCON0
    CALL    GECIKME_ADC_SETUP
    
    ; First Read (Dummy) - Clean the capacitor
    BSF     ADCON0, GO
WT_LDR1
    BTFSC   ADCON0, GO      ; Wait for conversion
    GOTO    WT_LDR1
    MOVF    ADRESH, W       ; Read result but ignore it
    
    ; Second Read (Real)
    BSF     ADCON0, GO
WT_LDR2
    BTFSC   ADCON0, GO
    GOTO    WT_LDR2
    
    MOVF    ADRESH, W
    MOVWF   TEMP_MATH
    
    ; Check if value changed to reduce noise
    MOVF    LDR_VAL, W
    SUBWF   TEMP_MATH, W
    BTFSC   STATUS, Z
    GOTO    LDR_SKIP        ; If same, skip update
    MOVF    TEMP_MATH, W
    MOVWF   LDR_VAL         ; Update LDR variable
LDR_SKIP

    ; --- Read Potentiometer (Channel 1) ---
    MOVLW   B'10001001'     ; Select AN1 (Pot)
    MOVWF   ADCON0
    CALL    GECIKME_ADC_SETUP
    
    ; First Read (Dummy)
    BSF     ADCON0, GO
WT_POT1
    BTFSC   ADCON0, GO
    GOTO    WT_POT1
    MOVF    ADRESH, W       ; Ignore
    
    ; Second Read (Real)
    BSF     ADCON0, GO
WT_POT2
    BTFSC   ADCON0, GO
    GOTO    WT_POT2
    
    MOVF    ADRESH, W
    MOVWF   POT_VAL         ; Update Pot variable
    RETURN

; ==============================================================================
; STEP MOTOR CONTROL [R2.2.1-3]
; Moves the motor to match DESIRED_ST with CURRENT_ST.
; ==============================================================================
MOTOR_HAREKET
    MOVF    CURRENT_ST, W
    SUBWF   DESIRED_ST, W
    BTFSC   STATUS, Z       ; If Current == Desired
    RETURN                  ; Do nothing
    
    BTFSC   STATUS, C       ; If Desired > Current
    GOTO    MOVE_CW         ; Close (Clockwise)
    GOTO    MOVE_CCW        ; Open (Counter-Clockwise)

MOVE_CW
    CALL    STEP_CW         ; Rotate 1 step
    INCF    CURRENT_ST, F   ; Increase position [R2.2.1-2]
    RETURN
MOVE_CCW
    CALL    STEP_CCW        ; Rotate 1 step
    DECF    CURRENT_ST, F   ; Decrease position [R2.2.1-2]
    RETURN

; --- Motor Phase Logic ---
STEP_CW
    INCF    PHASE_STEP, F
    GOTO    DRIVE
STEP_CCW
    DECF    PHASE_STEP, F
    GOTO    DRIVE

DRIVE
    MOVF    PHASE_STEP, W
    ANDLW   0x03            ; Keep it between 0-3
    CALL    STEP_TABLE      ; Get the bit pattern
    MOVWF   TEMP_MATH
    
    ; Write to PORTB but protect the LCD pins (RB4-RB7)
    MOVF    PORTB, W
    ANDLW   B'11110000'     
    IORWF   TEMP_MATH, W
    MOVWF   PORTB
    CALL    GECIKME_MOTOR   ; Speed delay
    RETURN

STEP_TABLE
    ADDWF   PCL, F
    RETLW   B'00000001'
    RETLW   B'00000010'
    RETLW   B'00000100'
    RETLW   B'00001000'

; ==============================================================================
; UART COMMAND HANDLER [R2.2.6-1]
; Receives commands from PC and sends responses.
; ==============================================================================
UART_DINLE_VE_ISLE
    BANKSEL PIR1
    BTFSS   PIR1, RCIF      ; Is data received?
    RETURN                  ; No, return
    
    BANKSEL RCSTA
    BTFSC   RCSTA, OERR     ; Check for error
    GOTO    UART_ERR
    
    BANKSEL RCREG
    MOVF    RCREG, W        ; Read the data
    MOVWF   UART_TEMP
    BANKSEL 0
    
    ; --- Check Command ID ---
    
    ; Request: Desired Curtain Low Byte (0x01)
    MOVLW   0x01
    SUBWF   UART_TEMP, W
    BTFSC   STATUS, Z
    GOTO    TX_DESIRED_LOW
    
    ; Request: Desired Curtain High Byte (0x02)
    MOVLW   0x02
    SUBWF   UART_TEMP, W
    BTFSC   STATUS, Z
    GOTO    TX_DESIRED_HIGH
    
    ; Request: Light Low Byte (0x07)
    MOVLW   0x07
    SUBWF   UART_TEMP, W
    BTFSC   STATUS, Z
    GOTO    TX_LIGHT_LOW
    
    ; Request: Light High Byte (0x08)
    MOVLW   0x08
    SUBWF   UART_TEMP, W
    BTFSC   STATUS, Z
    GOTO    TX_LIGHT_HIGH
    
    ; Set Command: 10xxxxxx or 11xxxxxx
    MOVF    UART_TEMP, W
    ANDLW   B'11000000'
    XORLW   B'10000000'
    BTFSC   STATUS, Z
    GOTO    UART_SET_LOW
    
    MOVF    UART_TEMP, W
    ANDLW   B'11000000'
    XORLW   B'11000000'
    BTFSC   STATUS, Z
    GOTO    UART_SET_HIGH
    
    ; Dummy responses for other commands (0x03, 0x04...)
    MOVLW   0x03
    SUBWF   UART_TEMP, W
    BTFSC   STATUS, Z
    GOTO    TX_DUMMY
    MOVLW   0x04
    SUBWF   UART_TEMP, W
    BTFSC   STATUS, Z
    GOTO    TX_DUMMY
    MOVLW   0x05
    SUBWF   UART_TEMP, W
    BTFSC   STATUS, Z
    GOTO    TX_DUMMY
    MOVLW   0x06
    SUBWF   UART_TEMP, W
    BTFSC   STATUS, Z
    GOTO    TX_DUMMY
    
    RETURN

; --- Send Responses ---
TX_DESIRED_LOW
    MOVLW   D'0'            ; Fractional part is 0
    GOTO    TX_W
TX_DESIRED_HIGH
    MOVF    CURRENT_ST, W   ; Send current status
    GOTO    TX_W
TX_LIGHT_LOW
    MOVLW   D'0'
    GOTO    TX_W
TX_LIGHT_HIGH
    MOVF    LDR_VAL, W      ; Send LDR value
    GOTO    TX_W
TX_DUMMY
    MOVLW   D'0'
    GOTO    TX_W

TX_W
    BANKSEL PIR1
WT_TX
    BTFSS   PIR1, TXIF      ; Wait until TX buffer is empty
    GOTO    WT_TX
    BANKSEL TXREG
    MOVWF   TXREG           ; Send byte
    BANKSEL 0
    RETURN

; --- Handle Set Commands ---
UART_SET_LOW
    MOVF    UART_TEMP, W
    ANDLW   B'00111111'     ; Get 6 bits
    MOVWF   UART_LOW_BYTE
    RETURN

UART_SET_HIGH
    MOVLW   D'2'            ; Switch to PC Mode
    MOVWF   SYSTEM_MODE
    MOVF    UART_TEMP, W
    ANDLW   B'00111111'     ; Get 6 bits
    MOVWF   DESIRED_ST      ; Update Target Position
    RETURN

UART_ERR
    BCF     RCSTA, CREN     ; Reset Receiver
    BSF     RCSTA, CREN
    RETURN

; ==============================================================================
; DISPLAY UPDATE [R2.2.5-1]
; Show values on the LCD.
; ==============================================================================
EKRANI_GUNCELLE
    ; Only update if values changed (prevents flicker)
    MOVF    CURRENT_ST, W
    XORWF   LAST_DISP_ST, W
    BTFSS   STATUS, Z
    GOTO    YAZDIR
    MOVF    LDR_VAL, W
    XORWF   LAST_LDR, W
    BTFSS   STATUS, Z
    GOTO    YAZDIR
    RETURN

YAZDIR
    ; Save new values
    MOVF    CURRENT_ST, W
    MOVWF   LAST_DISP_ST
    MOVF    LDR_VAL, W
    MOVWF   LAST_LDR
    
    ; Write Mode (M, A, P)
    MOVLW   0x86
    CALL    LCD_KOMUT
    
    MOVF    SYSTEM_MODE, W
    SUBLW   D'2'
    BTFSC   STATUS, Z
    GOTO    W_PC
    BTFSC   SW_MAN
    GOTO    W_MAN
    GOTO    W_AUTO

W_PC
    MOVLW   'P'
    CALL    LCD_VERI
    MOVLW   'C'
    CALL    LCD_VERI
    GOTO    W_VALS
W_MAN
    MOVLW   'M'
    CALL    LCD_VERI
    MOVLW   'A'
    CALL    LCD_VERI
    GOTO    W_VALS
W_AUTO
    MOVLW   'O'
    CALL    LCD_VERI
    MOVLW   'T'
    CALL    LCD_VERI

W_VALS
    ; Write Light Value
    MOVLW   0xC2
    CALL    LCD_KOMUT
    MOVF    LDR_VAL, W
    CALL    SAYI_BAS
    
    ; Write Curtain %
    MOVLW   0xCB
    CALL    LCD_KOMUT
    MOVF    CURRENT_ST, W
    CALL    SAYI_63_TO_PERCENT
    CALL    SAYI_BAS
    RETURN

; Helper to keep 0 for fractional
SAYI_0_255_TO_PERCENT
    MOVWF   BIN_L
    RETURN

; Convert 0-63 (Raw) to 0-100 (%)
SAYI_63_TO_PERCENT
    MOVWF   BIN_L
    MOVWF   TEMP_MATH
    BCF     STATUS, C
    RRF     TEMP_MATH, F
    MOVF    TEMP_MATH, W
    ADDWF   BIN_L, F        ; Add half
    
    BCF     STATUS, C
    RRF     TEMP_MATH, F
    BCF     STATUS, C
    RRF     TEMP_MATH, F
    BCF     STATUS, C
    RRF     TEMP_MATH, W
    ADDWF   BIN_L, F        ; Add small correction
    
    MOVF    BIN_L, W
    RETURN

; Display Number (BCD)
SAYI_BAS
    MOVWF   BIN_L
    CLRF    YUZ_H
    CLRF    ON_H
    CLRF    BIR_H
L_Y
    MOVLW   D'100'
    SUBWF   BIN_L, W
    BTFSS   STATUS, C
    GOTO    L_O
    MOVWF   BIN_L
    INCF    YUZ_H, F
    GOTO    L_Y
L_O
    MOVLW   D'10'
    SUBWF   BIN_L, W
    BTFSS   STATUS, C
    GOTO    L_B
    MOVWF   BIN_L
    INCF    ON_H, F
    GOTO    L_O
L_B
    MOVF    BIN_L, W
    MOVWF   BIR_H
    
    ; Convert digits to ASCII and send to LCD
    MOVF    YUZ_H, W
    ADDLW   0x30
    CALL    LCD_VERI
    MOVF    ON_H, W
    ADDLW   0x30
    CALL    LCD_VERI
    MOVF    BIR_H, W
    ADDLW   0x30
    CALL    LCD_VERI
    RETURN

; --- Delay Functions ---
GECIKME_MOTOR
    MOVLW   D'200'
    MOVWF   SAYAC2
G_M_OUTER
    MOVLW   D'200'
    MOVWF   SAYAC1
G_M_INNER
    DECFSZ  SAYAC1, F
    GOTO    G_M_INNER
    DECFSZ  SAYAC2, F
    GOTO    G_M_OUTER
    RETURN

GECIKME_ADC_SETUP
    MOVLW   D'50'
    MOVWF   SAYAC1
G_ADC
    DECFSZ  SAYAC1, F
    GOTO    G_ADC
    RETURN

; --- LCD Functions ---
LCD_INIT
    CALL    GECIKME_MOTOR
    MOVLW   0x38            ; 8-bit, 2 lines
    CALL    LCD_KOMUT
    MOVLW   0x0C            ; Display ON
    CALL    LCD_KOMUT
    MOVLW   0x01            ; Clear Display
    CALL    LCD_KOMUT
    CALL    GECIKME_MOTOR
    RETURN

LCD_KOMUT
    MOVWF   PORTD
    BCF     RS
    BSF     EN
    NOP
    BCF     EN
    CALL    G_LCD
    RETURN

LCD_VERI
    MOVWF   PORTD
    BSF     RS
    BSF     EN
    NOP
    BCF     EN
    CALL    G_LCD
    RETURN

G_LCD
    MOVLW   D'100'
    MOVWF   SAYAC1
G_LCD_LOOP
    DECFSZ  SAYAC1, F
    GOTO    G_LCD_LOOP
    RETURN

EKRAN_SABLON
    ; Draw the fixed text on LCD
    MOVLW   0x80
    CALL    LCD_KOMUT
    MOVLW   'M'
    CALL    LCD_VERI
    MOVLW   'O'
    CALL    LCD_VERI
    MOVLW   'D'
    CALL    LCD_VERI
    MOVLW   ':'
    CALL    LCD_VERI
    MOVLW   0xC0
    CALL    LCD_KOMUT
    MOVLW   'L'
    CALL    LCD_VERI
    MOVLW   ':'
    CALL    LCD_VERI
    MOVLW   0xC9
    CALL    LCD_KOMUT
    MOVLW   'C'
    CALL    LCD_VERI
    MOVLW   ':'
    CALL    LCD_VERI
    RETURN

    END