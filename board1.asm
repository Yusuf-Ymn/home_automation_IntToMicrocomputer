;=============================================================================
; UNIVERSITY: ESOGU - Electrical & Electronics / Computer Engineering
; COURSE:     Introduction to Microcomputers - Term Project
; FILE:       Board1_Diamond_UART.asm (Board #1)
;
; DESCRIPTION:
;    This code controls the Home Air Conditioner System (Board #1).
;    It manages Temperature Control, Keypad, Display, and UART communication.
;
; REQUIREMENTS MET:
;    [R2.1.1] Temperature Control (Heater/Cooler logic)
;    [R2.1.2] Keypad Input (Enter desired temp)
;    [R2.1.3] Display (Show Temp/Fan Speed)
;    [R2.1.4] UART Communication (PC Interface)
;
; AUTHORS:
;    1. Yusuf Yaman 152120221075
;    2. Yigit Ata 152120221106
;    3. Dogancan Kucuk 151220212099
;=============================================================================

    LIST P=16F877A
    INCLUDE "P16F877A.INC"

    __CONFIG _FOSC_XT & _WDTE_OFF & _PWRTE_ON & _BOREN_ON & _LVP_OFF & _CPD_OFF & _WRT_OFF & _CP_OFF

    ;----------------------------- REGISTER MAP ----------------------------------
    ; --- COMMON RAM (0x70-0x7F) ---
    CBLOCK 0x70
        W_TEMP              ; Context saving for ISR
        STATUS_TEMP         ; Context saving for ISR
        DIGIT_3_VAL         ; Display digit 3 data
        DIGIT_4_VAL         ; Display digit 4 data
        DELAY_VAR1          ; Delay loop variable
        DELAY_VAR2          ; Delay loop variable
        DISP_LOOP_CNT       ; Loop counter for display refresh
        STABLE_CNT          ; Counter for keypad debounce
        UART_DAT            ; [R2.1.4] Stores received UART data
    ENDC

    ; --- BANK 0 RAM ---
    CBLOCK 0x20
        TEMP_VAL            ; [R2.1.1-4] Current Ambient Temperature
        DESIRED_TEMP        ; [R2.1.1-1] User Desired Temperature
        FAN_SPEED_RPS       ; [R2.1.1-5] Fan Speed (Rotations Per Second)
        DISPLAY_MODE        ; 0: Normal, 1: Input Mode
        SHOW_FAN_FLAG       ; Toggle flag for Display (Temp vs Fan)
        KEY_VAL             ; Current key code
        KEY_VAL_TEMP        ; Temp key code for debounce
        INPUT_VAL           ; Temp variable for number entry
        INPUT_DIGIT_CNT     ; Count of digits entered
        TIMER0_CNT          ; Timer0 overflow counter (Software Timer)
        DISP_TOGGLE_CNT     ; Counter to toggle screen content
        SETTLE_LOOP         ; Loop for signal settling
    ENDC

    #define HEATER_PIN  PORTC, 1    ; [R2.1.1] Output for Heater
    #define COOLER_PIN  PORTC, 2    ; [R2.1.1] Output for Cooler

    ORG 0x000
    GOTO MAIN

    ORG 0x004
    GOTO ISR_ROUTINE

;=============================================================================
; MAIN PROGRAM
;=============================================================================
MAIN:
    ; --- BANK 1 Configuration ---
    BANKSEL TRISA
    MOVLW   b'10001110'     ; Configure ADCON1 (Right justified)
    MOVWF   ADCON1
    
    CLRF    TRISD           ; PORTD is Output (7-Segment Display)
    
    ; --- UART CONFIGURATION [R2.1.4] ---
    ; RC7 is RX (Input), RC6 is TX (Output)
    MOVLW   b'10000001'     
    MOVWF   TRISC
    ; -----------------------------------

    CLRF    TRISA
    BSF     TRISA, 0        ; RA0 is Input (LM35 Temperature Sensor)
    
    MOVLW   b'11110000'     ; PORTB: Rows=Output, Cols=Input (Keypad)
    MOVWF   TRISB
    BCF     OPTION_REG, 7   ; Enable PortB Pull-ups

    MOVLW   b'00000111'     ; Timer0 Prescaler 1:256
    MOVWF   OPTION_REG

    ; --- BANK 0 Configuration ---
    BANKSEL PORTA
    CLRF    PORTA
    CLRF    PORTD
    CLRF    PORTC

    ; Initialize Variables
    MOVLW   d'25'
    MOVWF   DESIRED_TEMP    ; Default desired temp is 25C
    CLRF    DISPLAY_MODE
    CLRF    SHOW_FAN_FLAG
    
    MOVLW   d'15'
    MOVWF   TIMER0_CNT
    MOVLW   d'30'
    MOVWF   DISP_TOGGLE_CNT

    MOVLW   b'10000001'     ; ADCON0: Fosc/32, Channel 0, On
    MOVWF   ADCON0
    
    CLRF    TMR1L           ; Clear Timer1 (Used for Fan Speed)
    CLRF    TMR1H
    MOVLW   b'00000111'     ; Enable Timer1, External Clock
    MOVWF   T1CON

    ; --- UART INITIALIZATION ---
    CALL    UART_INIT       ; Initialize Serial Communication
    ; ---------------------------

    BSF     INTCON, T0IE    ; Enable Timer0 Interrupt
    BSF     INTCON, GIE     ; Enable Global Interrupts

ANA_DONGU:                  ; Main Loop
    ; --- UART POLLING [R2.1.4-1] ---
    CALL    UART_HANDLER    ; Check if PC sent a command
    ; -------------------------------

    ; 1. Process Keypad Inputs [R2.1.2]
    CALL    KEYPAD_ISLE
    
    ; 2. Sensor and Control Logic [R2.1.1]
    MOVF    DISPLAY_MODE, F
    BTFSC   STATUS, Z       ; Only run control in Normal Mode (0)
    CALL    SISTEM_KONTROL

    ; 3. Prepare Data for Display
    CALL    EKRAN_VERI_HAZIRLA

    ; 4. Refresh Display [R2.1.3]
    MOVLW   d'5'
    MOVWF   DISP_LOOP_CNT
DISP_L:
    CALL    UART_HANDLER    ; Keep checking UART while driving display
    CALL    EKRANI_GOSTER   ; Show digits on 7-Segment
    DECFSZ  DISP_LOOP_CNT, F
    GOTO    DISP_L
    
    GOTO    ANA_DONGU

;=============================================================================
; SYSTEM CONTROL [R2.1.1]
;=============================================================================
SISTEM_KONTROL:
    CALL    ADC_OKU                 ; Read Ambient Temperature [R2.1.1-4]
    MOVF    TEMP_VAL, W
    SUBWF   DESIRED_TEMP, W
    BTFSS   STATUS, C               ; Check if Desired < Ambient
    GOTO    SOGUTUCU_AC             ; Logic for Cooling
    
    ; [R2.1.1-3] If Desired > Ambient -> Heater ON
    BSF     HEATER_PIN              
    BCF     COOLER_PIN
    RETURN
SOGUTUCU_AC:
    ; [R2.1.1-2] If Desired < Ambient -> Cooler ON
    BCF     HEATER_PIN
    BSF     COOLER_PIN              
    RETURN

;=============================================================================
; KEYPAD PROCESSING [R2.1.2]
;=============================================================================
KEYPAD_ISLE:
    ; 1. Scan for any key press
    CALL    SCAN_KEYPAD_SAFE
    MOVWF   KEY_VAL
    XORLW   0xFF
    BTFSC   STATUS, Z       ; If 0xFF, no key pressed
    RETURN

    ; 2. Key detected (Debounce wait)
    CALL    WAIT_AND_REFRESH
    
    ; 3. Verify key press (Double check)
    CALL    SCAN_KEYPAD_SAFE
    MOVWF   KEY_VAL_TEMP
    MOVF    KEY_VAL, W
    SUBWF   KEY_VAL_TEMP, W
    BTFSS   STATUS, Z       ; If not matching, it was noise
    RETURN

    ; --- VALID KEY PRESSED ---
    MOVF    KEY_VAL, W
    
    XORLW   d'10'           ; Check for 'A' Key
    BTFSC   STATUS, Z
    GOTO    BASLAT_GIRIS    ; [R2.1.2-1] Start Input Mode
    
    MOVF    KEY_VAL, W      
    XORLW   d'12'           ; Check for '#' Key
    BTFSC   STATUS, Z
    GOTO    ONAYLA_GIRIS    ; [R2.1.2-2] Confirm Input
    
    MOVF    KEY_VAL, W
    SUBLW   d'9'            ; Check if it is a Digit (0-9)
    BTFSC   STATUS, C       
    GOTO    RAKAM_ISLE      ; Process Digit
    
    GOTO    BEKLE_BIRAKMA   ; Ignore other keys

BASLAT_GIRIS:
    MOVLW   d'1'
    MOVWF   DISPLAY_MODE    ; Set mode to Input
    CLRF    INPUT_VAL
    CLRF    INPUT_DIGIT_CNT
    GOTO    BEKLE_BIRAKMA

ONAYLA_GIRIS:
    MOVF    DISPLAY_MODE, F
    BTFSC   STATUS, Z       ; If not in input mode, ignore
    GOTO    BEKLE_BIRAKMA
    
    MOVF    INPUT_VAL, W    ; [R2.1.2-4] Save entered value
    MOVWF   DESIRED_TEMP
    CLRF    DISPLAY_MODE    ; Return to Normal Mode
    GOTO    BEKLE_BIRAKMA

RAKAM_ISLE:
    MOVF    DISPLAY_MODE, F
    BTFSC   STATUS, Z       ; If not in input mode, ignore
    GOTO    BEKLE_BIRAKMA
    
    MOVLW   d'2'            ; Limit input to 2 digits
    SUBWF   INPUT_DIGIT_CNT, W
    BTFSC   STATUS, C
    GOTO    BEKLE_BIRAKMA
    
    MOVF    INPUT_DIGIT_CNT, F
    BTFSS   STATUS, Z
    GOTO    IKINCI_HANE     ; Process second digit
    
    MOVF    KEY_VAL, W      ; Store first digit
    MOVWF   INPUT_VAL
    INCF    INPUT_DIGIT_CNT, F
    GOTO    BEKLE_BIRAKMA

IKINCI_HANE:
    ; Logic to shift decimal (Input = Input * 10 + NewKey)
    MOVF    INPUT_VAL, W
    MOVWF   DELAY_VAR1
    BCF     STATUS, C
    RLF     INPUT_VAL, F    ; x2
    BCF     STATUS, C
    RLF     INPUT_VAL, F    ; x4
    MOVF    INPUT_VAL, W
    ADDWF   DELAY_VAR1, W   ; x5
    BCF     STATUS, C
    MOVWF   DELAY_VAR1
    RLF     DELAY_VAR1, F   ; x10
    MOVF    DELAY_VAR1, W
    ADDWF   KEY_VAL, W      ; Add new digit
    MOVWF   INPUT_VAL
    INCF    INPUT_DIGIT_CNT, F

; --- WAIT FOR KEY RELEASE ---
BEKLE_BIRAKMA:
    MOVLW   d'10'
    MOVWF   STABLE_CNT
CHECK_REL:
    CALL    EKRANI_GOSTER   ; Keep display alive
    CALL    SCAN_KEYPAD_SAFE
    XORLW   0xFF
    BTFSC   STATUS, Z       ; Is key released?
    GOTO    DEC_REL_CNT
    
    MOVLW   d'10'           ; Reset counter if key is still down
    MOVWF   STABLE_CNT
    GOTO    CHECK_REL

DEC_REL_CNT:
    DECFSZ  STABLE_CNT, F
    GOTO    CHECK_REL
    RETURN

;=============================================================================
; HELPER SUBROUTINES
;=============================================================================
WAIT_AND_REFRESH:
    MOVLW   d'6'
    MOVWF   DISP_LOOP_CNT
W_R_L:
    CALL    EKRANI_GOSTER   
    DECFSZ  DISP_LOOP_CNT, F
    GOTO    W_R_L
    RETURN

SCAN_KEYPAD_SAFE:
    ; Scans the matrix keypad rows and columns
    BANKSEL PORTB
    
    ; Row 1
    MOVLW   b'11111110'     
    MOVWF   PORTB
    CALL    SETTLE_TIME
    BTFSS   PORTB, 4
    RETLW   d'1'
    BTFSS   PORTB, 5
    RETLW   d'2'
    BTFSS   PORTB, 6
    RETLW   d'3'
    BTFSS   PORTB, 7
    RETLW   d'10' ; 'A'

    ; Row 2
    MOVLW   b'11111101'     
    MOVWF   PORTB
    CALL    SETTLE_TIME
    BTFSS   PORTB, 4
    RETLW   d'4'
    BTFSS   PORTB, 5
    RETLW   d'5'
    BTFSS   PORTB, 6
    RETLW   d'6'
    BTFSS   PORTB, 7
    RETLW   d'11' ; 'B'

    ; Row 3
    MOVLW   b'11111011'     
    MOVWF   PORTB
    CALL    SETTLE_TIME
    BTFSS   PORTB, 4
    RETLW   d'7'
    BTFSS   PORTB, 5
    RETLW   d'8'
    BTFSS   PORTB, 6
    RETLW   d'9'
    BTFSS   PORTB, 7
    RETLW   d'13' ; 'C'

    ; Row 4
    MOVLW   b'11110111'     
    MOVWF   PORTB
    CALL    SETTLE_TIME
    BTFSS   PORTB, 4
    RETLW   d'14' ; '*'
    BTFSS   PORTB, 5
    RETLW   d'0'
    BTFSS   PORTB, 6
    RETLW   d'12' ; '#'
    BTFSS   PORTB, 7
    RETLW   d'15' ; 'D'
    RETLW   0xFF  ; No key

SETTLE_TIME:
    MOVLW   d'100'          ; Short delay for signal stability
    MOVWF   SETTLE_LOOP
ST_L:
    NOP
    DECFSZ  SETTLE_LOOP, F
    GOTO    ST_L
    RETURN

EKRAN_VERI_HAZIRLA:
    ; Determines what to show on display (Temp vs Fan vs Input)
    MOVF    DISPLAY_MODE, F
    BTFSS   STATUS, Z
    GOTO    MOD_GIRIS_G     ; Show Input
    BTFSC   SHOW_FAN_FLAG, 0
    GOTO    MOD_FAN_G       ; Show Fan Speed
    MOVF    TEMP_VAL, W     ; Show Temperature
    CALL    HEX_TO_DEC
    RETURN
MOD_FAN_G:
    MOVF    FAN_SPEED_RPS, W
    CALL    HEX_TO_DEC
    RETURN
MOD_GIRIS_G:
    MOVF    INPUT_VAL, W
    CALL    HEX_TO_DEC
    RETURN

HEX_TO_DEC:
    ; Splits byte into two decimal digits (Tens and Ones)
    MOVWF   DIGIT_4_VAL     
    CLRF    DIGIT_3_VAL
ONLAR_LP:
    MOVLW   d'10'
    SUBWF   DIGIT_4_VAL, W
    BTFSS   STATUS, C
    GOTO    HTD_EXIT
    MOVWF   DIGIT_4_VAL
    INCF    DIGIT_3_VAL, F
    GOTO    ONLAR_LP
HTD_EXIT:
    RETURN

EKRANI_GOSTER:
    ; Multiplexing for 7-Segment Display
    BANKSEL PORTA
    
    ; Show Tens Digit
    MOVF    DIGIT_3_VAL, W
    CALL    GET_SEG
    MOVWF   PORTD
    BSF     PORTA, 3        ; Enable Digit 3
    CALL    DELAY_MS
    BCF     PORTA, 3
    
    ; Show Ones Digit
    MOVF    DIGIT_4_VAL, W
    CALL    GET_SEG
    MOVWF   PORTD
    BSF     PORTA, 5        ; Enable Digit 4 (Simulated mapping)
    CALL    DELAY_MS
    BCF     PORTA, 5
    RETURN

GET_SEG:
    ; Look-up table for 7-Segment Patterns (Common Cathode)
    ADDWF   PCL, F
    RETLW   0x3F ; 0
    RETLW   0x06 ; 1
    RETLW   0x5B ; 2
    RETLW   0x4F ; 3
    RETLW   0x66 ; 4
    RETLW   0x6D ; 5
    RETLW   0x7D ; 6
    RETLW   0x07 ; 7
    RETLW   0x7F ; 8
    RETLW   0x6F ; 9
    RETLW   0x77 ; A
    RETLW   0x7C ; b
    RETLW   0x00 ; # (Blank)
    RETURN

DELAY_MS:
    ; Simple Delay Loop
    MOVLW   d'5'
    MOVWF   DELAY_VAR2
DY_L1:
    MOVLW   d'200'
    MOVWF   DELAY_VAR1
DY_L2:
    DECFSZ  DELAY_VAR1, F
    GOTO    DY_L2
    DECFSZ  DELAY_VAR2, F
    GOTO    DY_L1
    RETURN

;=============================================================================
; ADC READ [R2.1.1-4]
;=============================================================================
ADC_OKU:
    BANKSEL ADCON0      ; Select Bank 0
    BSF     ADCON0, GO  ; Start Conversion
ADC_WAIT:
    BTFSC   ADCON0, GO  ; Wait for finish
    GOTO    ADC_WAIT
    
    BANKSEL ADRESL      ; Select Bank 1
    MOVF    ADRESL, W   ; Get Lower 8 bits (Right Justified)
    
    BANKSEL PORTA       ; Return to Bank 0
    MOVWF   TEMP_VAL    ; Store Result
    BCF     STATUS, C
    RRF     TEMP_VAL, F ; Divide by 2 (Calibration for LM35/ADC)
    RETURN

;=============================================================================
; ISR - INTERRUPT SERVICE ROUTINE
;=============================================================================
ISR_ROUTINE:
    MOVWF   W_TEMP          ; Save Context
    SWAPF   STATUS, W
    MOVWF   STATUS_TEMP
    
    BANKSEL PORTA           ; Force Bank 0
    
    BCF     INTCON, T0IF    ; Clear Timer0 Flag
    DECFSZ  TIMER0_CNT, F   ; Decrement software counter
    GOTO    ISR_RET
    
    ; --- 1 Second Elapsed ---
    MOVLW   d'15'           ; Reset software counter
    MOVWF   TIMER0_CNT
    
    MOVF    TMR1L, W        ; Read Fan Pulses [R2.1.1-5]
    MOVWF   FAN_SPEED_RPS
    CLRF    TMR1L           ; Reset Counter
    CLRF    TMR1H
    
    ; Toggle Display Mode (Temp <-> Fan)
    DECFSZ  DISP_TOGGLE_CNT, F
    GOTO    ISR_RET
    MOVLW   d'30'
    MOVWF   DISP_TOGGLE_CNT
    MOVLW   1
    XORWF   SHOW_FAN_FLAG, F ; Toggle Flag

ISR_RET:
    SWAPF   STATUS_TEMP, W  ; Restore Context
    MOVWF   STATUS
    SWAPF   W_TEMP, F
    SWAPF   W_TEMP, W
    RETFIE

;=============================================================================
; UART MODULE [R2.1.4]
;=============================================================================
UART_INIT:
    ; Configure for 9600 Baud @ 4MHz
    BANKSEL SPBRG
    MOVLW   d'25'
    MOVWF   SPBRG
    
    MOVLW   b'00100100'     ; TXEN=1, BRGH=1
    MOVWF   TXSTA
    
    BANKSEL RCSTA
    MOVLW   b'10010000'     ; SPEN=1, CREN=1
    MOVWF   RCSTA
    
    BANKSEL PORTA           ; Return to Bank 0
    RETURN

UART_HANDLER:
    BANKSEL PIR1            ; Check in Bank 0
    BTFSS   PIR1, RCIF      ; Is Data Received?
    RETURN                  ; No data
    
    ; Data Received
    MOVF    RCREG, W        ; Read Data
    MOVWF   UART_DAT
    CALL    PARSE_COMMAND   ; Handle Command
    RETURN

UART_SEND_BYTE:
    ; Sends W register via UART
    BANKSEL TXSTA
WT_TX:
    BTFSS   TXSTA, TRMT     ; Wait for Buffer Empty
    GOTO    WT_TX
    
    BANKSEL TXREG
    MOVWF   TXREG           ; Send Data
    BANKSEL PORTA           ; Return to Bank 0
    RETURN

; Protocol Handler
PARSE_COMMAND:
    ; 1. GET Desired Temp Low (Fractional) - Cmd: 0x01
    MOVF    UART_DAT, W
    XORLW   0x01
    BTFSC   STATUS, Z
    GOTO    SEND_ZERO       ; Fractional part is 0 in this logic

    ; 2. GET Desired Temp High (Integral) - Cmd: 0x02
    MOVF    UART_DAT, W
    XORLW   0x02
    BTFSC   STATUS, Z
    GOTO    SEND_DESIRED

    ; 3. GET Ambient Temp Low (Fractional) - Cmd: 0x03
    MOVF    UART_DAT, W
    XORLW   0x03
    BTFSC   STATUS, Z
    GOTO    SEND_ZERO       ; ADC reads integer

    ; 4. GET Ambient Temp High (Integral) - Cmd: 0x04
    MOVF    UART_DAT, W
    XORLW   0x04
    BTFSC   STATUS, Z
    GOTO    SEND_AMBIENT

    ; 5. GET Fan Speed - Cmd: 0x05
    MOVF    UART_DAT, W
    XORLW   0x05
    BTFSC   STATUS, Z
    GOTO    SEND_FAN

    ; 6. SET Desired Temp High (Integral) - Cmd: 11xxxxxx
    MOVF    UART_DAT, W
    ANDLW   b'11000000'     ; Mask top 2 bits
    XORLW   b'11000000'     ; Check if it is '11'
    BTFSC   STATUS, Z
    GOTO    SET_DESIRED_CMD
    
    RETURN

SEND_ZERO:
    MOVLW   d'0'
    CALL    UART_SEND_BYTE
    RETURN

SEND_DESIRED:
    MOVF    DESIRED_TEMP, W
    CALL    UART_SEND_BYTE
    RETURN

SEND_AMBIENT:
    MOVF    TEMP_VAL, W
    CALL    UART_SEND_BYTE
    RETURN

SEND_FAN:
    MOVF    FAN_SPEED_RPS, W
    CALL    UART_SEND_BYTE
    RETURN

SET_DESIRED_CMD:
    ; Parse 6-bit data from 11xxxxxx
    MOVF    UART_DAT, W
    ANDLW   b'00111111'     ; Clear prefix bits
    MOVWF   DESIRED_TEMP    ; Update Desired Temp
    RETURN

    END
