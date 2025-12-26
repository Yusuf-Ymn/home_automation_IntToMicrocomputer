; BOARD #1: AKILLI ?KL?MLEND?RME VE HABERLE?ME S?STEM? - N?HA? SÜRÜM
    
    LIST P=16F877A
    INCLUDE "P16F877A.INC"

    __CONFIG _CP_OFF & _WDT_OFF & _PWRTE_ON & _XT_OSC & _LVP_OFF

;--- BELLEK TANIMLARI ---
    CBLOCK 0x20
        W_TEMP, STATUS_TEMP     
        AMBIENT_TEMP_INT, AMBIENT_TEMP_FRAC
        DESIRED_TEMP_INT, DESIRED_TEMP_FRAC
        FAN_SPEED_RPS, INPUT_MODE, FRACTION_MODE
        SEC_2_TIMER, DISP_STATE, CURR_VALUE, CURR_FRAC
        DIG_H, DIG_L, TEMP_INT, TEMP_FRAC, KEY_VAL
        TEMP_VAR, DELAY_VAR, TEMP_DIGIT_H, TEMP_DIGIT_F
    ENDC

#DEFINE HEATER      PORTD, 0
#DEFINE COOLER      PORTD, 1
#DEFINE SEG_PORT    PORTD
#DEFINE DIGIT1      PORTA, 1
#DEFINE DIGIT2      PORTA, 2

    ORG 0x00
    GOTO INITIALIZE

    ORG 0x04
    GOTO ISR_ROUTINE

;--- S?STEM BA?LATMA ---
INITIALIZE:
    BANKSEL TRISA
    MOVLW   B'00000001'         ; RA0 Analog Giri?
    MOVWF   TRISA
    CLRF    TRISD               ; PORTD Ç?k??
    MOVLW   B'11110001'         ; RB0: Kesme, RB1-3: Sütun, RB4-7: Sat?r
    MOVWF   TRISB
    
    MOVLW   B'10001110'         ; ADCON1: RA0 Analog, Right Justified
    MOVWF   ADCON1
    
    MOVLW   .25                 ; 9600 Baud @ 4MHz SPBRG = 25
    MOVWF   SPBRG
    BSF     TXSTA, TXEN         ; Transmit Enable
    BCF     TXSTA, SYNC         ; Asynchronous
    
    BANKSEL RCSTA
    BSF     RCSTA, SPEN         ; Serial Port Enable
    BSF     RCSTA, CREN         ; Continuous Receive Enable
    
    BANKSEL INTCON
    MOVLW   B'10010000'         ; GIE ve INTE (RB0) aktif
    MOVWF   INTCON
    
    ; Ba?lang?ç De?erleri
    MOVLW   .25
    MOVWF   DESIRED_TEMP_INT
    CLRF    DESIRED_TEMP_FRAC
    CLRF    INPUT_MODE
    CLRF    DISP_STATE
    GOTO    MAIN_LOOP

;--- ANA DÖNGÜ ---
MAIN_LOOP:
    CALL    ADC_READ            ; Sensör oku
    CALL    HVAC_SYSTEM         ; Karar mekanizmas?
    CALL    UART_CONTROL        ; Board #2 ile haberle?me
    CALL    DISPLAY_ROTATION    ; 2sn'lik ekran geçi?leri
    CALL    SEG_MULTIPLEX       ; 7-Segment tarama
    GOTO    MAIN_LOOP

;--- SENSÖR VE HVAC ---
ADC_READ:
    BANKSEL ADCON0
    MOVLW   B'10000001'         ; CH0, Fosc/2, ADC ON
    MOVWF   ADCON0
    BSF     ADCON0, GO          ; Ba?lat
WAIT_ADC: 
    BTFSC   ADCON0, GO
    GOTO    WAIT_ADC
    MOVF    ADRESH, W
    MOVWF   AMBIENT_TEMP_INT    ; Ham veriyi kaydet
    RETURN

HVAC_SYSTEM:
    MOVF    AMBIENT_TEMP_INT, W
    SUBWF   DESIRED_TEMP_INT, W 
    BTFSC   STATUS, C           ; Desired >= Ambient ?
    GOTO    ACTIVATE_HEATER
    GOTO    ACTIVATE_COOLER

ACTIVATE_HEATER:
    BSF     HEATER
    BCF     COOLER
    CLRF    FAN_SPEED_RPS
    RETURN

ACTIVATE_COOLER:
    BCF     HEATER
    BSF     COOLER
    MOVLW   .15                 ; Standart Fan H?z?
    MOVWF   FAN_SPEED_RPS
    RETURN

;--- UART HABERLE?ME ---
UART_CONTROL:
    BTFSS   PIR1, RCIF
    RETURN
    MOVF    RCREG, W            ; Gelen komut
    MOVWF   TEMP_VAR
    
    XORLW   0x01
    BTFSC   STATUS, Z
    GOTO    S_D_FRAC
    
    MOVF    TEMP_VAR, W
    XORLW   0x02
    BTFSC   STATUS, Z
    GOTO    S_D_INT
    
    MOVF    TEMP_VAR, W
    XORLW   0x05
    BTFSC   STATUS, Z
    GOTO    S_F_RPS
    RETURN

S_D_FRAC:
    MOVF    DESIRED_TEMP_FRAC, W
    MOVWF   TXREG
    RETURN
S_D_INT:
    MOVF    DESIRED_TEMP_INT, W
    MOVWF   TXREG
    RETURN
S_F_RPS:
    MOVF    FAN_SPEED_RPS, W
    MOVWF   TXREG
    RETURN

;--- ISR ---

ISR_ROUTINE:
    MOVWF   W_TEMP
    SWAPF   STATUS, W
    MOVWF   STATUS_TEMP
    
    BTFSS   INTCON, INTF
    GOTO    ISR_EXIT

    MOVLW   .1
    MOVWF   INPUT_MODE
    CLRF    FRACTION_MODE
    CLRF    TEMP_INT
    CLRF    TEMP_FRAC

KEY_SCAN:
    ; Sat?r 1 (1,2,3)
    MOVLW   B'11101111'
    MOVWF   PORTB
    BTFSS   PORTB, 1
    MOVLW   .1
    BTFSS   PORTB, 2
    MOVLW   .2
    BTFSS   PORTB, 3
    MOVLW   .3
    CALL    PROCESS_KEY

    ; Sat?r 2 (4,5,6)
    MOVLW   B'11011111'
    MOVWF   PORTB
    BTFSS   PORTB, 1
    MOVLW   .4
    BTFSS   PORTB, 2
    MOVLW   .5
    BTFSS   PORTB, 3
    MOVLW   .6
    CALL    PROCESS_KEY

    ; Sat?r 3 (7,8,9)
    MOVLW   B'10111111'
    MOVWF   PORTB
    BTFSS   PORTB, 1
    MOVLW   .7
    BTFSS   PORTB, 2
    MOVLW   .8
    BTFSS   PORTB, 3
    MOVLW   .9
    CALL    PROCESS_KEY

    ; Sat?r 4 (*,0,#)
    MOVLW   B'01111111'
    MOVWF   PORTB
    BTFSS   PORTB, 1            ; * Tu?u (Ondal?k)
    GOTO    SET_FRAC
    BTFSS   PORTB, 2            ; 0 Tu?u
    MOVLW   .0
    CALL    PROCESS_KEY
    BTFSS   PORTB, 3            ; # Tu?u (Onay)
    GOTO    VERIFY_EXIT
    GOTO    KEY_SCAN

SET_FRAC:
    MOVLW   .1
    MOVWF   FRACTION_MODE
    CALL    WAIT_REL
    GOTO    KEY_SCAN

PROCESS_KEY:
    MOVWF   KEY_VAL
    BTFSC   FRACTION_MODE, 0
    GOTO    SAVE_FRAC
    
    ; Tam Say? X10 (X8 + X2)
    MOVF    TEMP_INT, W
    MOVWF   TEMP_VAR
    BCF     STATUS, C
    RLF     TEMP_VAR, F         ; x2
    RLF     TEMP_VAR, F         ; x4
    RLF     TEMP_VAR, F         ; x8
    BCF     STATUS, C
    RLF     TEMP_INT, W         ; W = x2
    ADDWF   TEMP_VAR, F         ; x8 + x2 = x10
    MOVF    KEY_VAL, W
    ADDWF   TEMP_VAR, W
    MOVWF   TEMP_INT
    GOTO    P_DONE

SAVE_FRAC:
    MOVF    KEY_VAL, W
    MOVWF   TEMP_FRAC

P_DONE:
    CALL    WAIT_REL
    RETURN

VERIFY_EXIT:
    ; 10-50 Derece S?n?r?
    MOVLW   .10
    SUBWF   TEMP_INT, W
    BTFSS   STATUS, C
    GOTO    ISR_FINISH          ; Hatal?: 10'dan küçük
    
    MOVLW   .51
    SUBWF   TEMP_INT, W
    BTFSC   STATUS, C
    GOTO    ISR_FINISH          ; Hatal?: 50'den büyük

    MOVF    TEMP_INT, W
    MOVWF   DESIRED_TEMP_INT
    MOVF    TEMP_FRAC, W
    MOVWF   DESIRED_TEMP_FRAC

ISR_FINISH:
    CLRF    INPUT_MODE
    BCF     INTCON, INTF
    CALL    WAIT_REL

ISR_EXIT:
    SWAPF   STATUS_TEMP, W
    MOVWF   STATUS
    SWAPF   W_TEMP, F
    SWAPF   W_TEMP, W
    RETFIE

WAIT_REL:
    MOVLW   B'11110000'
    MOVWF   PORTB
    MOVF    PORTB, W
    ANDLW   B'00001110'
    XORLW   B'00001110'
    BTFSS   STATUS, Z
    GOTO    WAIT_REL
    RETURN

;--- EKRAN YÖNET?M? ---
DISPLAY_ROTATION:
    INCF    SEC_2_TIMER, F
    MOVLW   .250
    SUBWF   SEC_2_TIMER, W
    BTFSS   STATUS, C
    RETURN
    CLRF    SEC_2_TIMER
    INCF    DISP_STATE, F
    MOVLW   .3
    SUBWF   DISP_STATE, W
    BTFSC   STATUS, C
    CLRF    DISP_STATE
    RETURN

SEG_MULTIPLEX:
    ; Hangi de?er gösterilecek?
    MOVF    DISP_STATE, W
    XORLW   .0
    BTFSC   STATUS, Z
    MOVF    DESIRED_TEMP_INT, W
    
    MOVF    DISP_STATE, W
    XORLW   .1
    BTFSC   STATUS, Z
    MOVF    AMBIENT_TEMP_INT, W
    
    MOVF    DISP_STATE, W
    XORLW   .2
    BTFSC   STATUS, Z
    MOVF    FAN_SPEED_RPS, W
    
    MOVWF   CURR_VALUE

    ; Basamaklara ay?r (Say? / 10)
    CLRF    DIG_H
    MOVF    CURR_VALUE, W
    MOVWF   TEMP_VAR
D_10:
    MOVLW   .10
    SUBWF   TEMP_VAR, W
    BTFSS   STATUS, C
    GOTO    D_END
    MOVWF   TEMP_VAR
    INCF    DIG_H, F
    GOTO    D_10
D_END:
    MOVF    TEMP_VAR, W
    MOVWF   DIG_L

    ; Sol Digit (Onlar)
    MOVF    DIG_H, W
    CALL    SEG_TABLE
    MOVWF   SEG_PORT
    BSF     DIGIT1
    CALL    DELAY_5MS
    BCF     DIGIT1
    
    ; Sa? Digit (Birler + Nokta)
    MOVF    DIG_L, W
    CALL    SEG_TABLE
    IORLW   B'10000000'         
    MOVWF   SEG_PORT
    BSF     DIGIT2
    CALL    DELAY_5MS
    BCF     DIGIT2
    RETURN

DELAY_5MS:
    MOVLW   .255
    MOVWF   DELAY_VAR
DLY: DECFSZ  DELAY_VAR, F
    GOTO    DLY
    RETURN

SEG_TABLE:
    ADDWF   PCL, F
    RETLW   B'00111111' ; 0
    RETLW   B'00000110' ; 1
    RETLW   B'01011011' ; 2
    RETLW   B'01001111' ; 3
    RETLW   B'01100110' ; 4
    RETLW   B'01101101' ; 5
    RETLW   B'01111101' ; 6
    RETLW   B'00000111' ; 7
    RETLW   B'01111111' ; 8
    RETLW   B'01101111' ; 9

    END