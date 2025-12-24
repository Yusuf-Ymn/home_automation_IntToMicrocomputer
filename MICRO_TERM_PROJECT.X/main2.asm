LIST P=16F877A
    INCLUDE "P16F877A.INC"

    __CONFIG _CP_OFF & _WDT_OFF & _BODEN_ON & _PWRTE_ON & _XT_OSC & _WRT_OFF & _LVP_OFF & _CPD_OFF

    CBLOCK 0x20
        SAYAC1, SAYAC2
        DESIRED_ST, CURRENT_ST          
        STEP_LOOP, BIN_SAYI            
        YUZLER, ONLAR, BIRLER
        LDR_VAL, POT_VAL, TEMP_MATH
        LAST_VAL, PHASE_STEP
    ENDC

#define RS PORTB, 4
#define EN PORTB, 5
#define MOD_SWITCH PORTA, 2

    ORG 0x00
    GOTO SETUP

SETUP
    BSF     STATUS, RP0
    CLRF    TRISD           
    MOVLW   B'11000000'     
    MOVWF   TRISB
    MOVLW   B'00000111'
    MOVWF   TRISA
    MOVLW   B'00000100'     
    MOVWF   ADCON1
    BCF     STATUS, RP0
    MOVLW   B'10000001'     
    MOVWF   ADCON0
    
    CLRF    PHASE_STEP
    MOVLW   B'0001'         
    MOVWF   PORTB
    CALL    GECIKME_KISA    
    CLRF    CURRENT_ST      
    MOVLW   0xFF
    MOVWF   LAST_VAL
    CALL    LCD_INIT
    GOTO    ANA_DONGU

ANA_DONGU
    BTFSC   MOD_SWITCH
    GOTO    MANUEL_OKU

OTOMATIK_OKU
    MOVLW   B'10000001'
    MOVWF   ADCON0
    CALL    GECIKME_KISA
    CALL    ADC_OKU
    MOVF    ADRESH, W
    SUBLW   D'255'          
    CALL    SCALE_LDR_100   
    MOVWF   LDR_VAL         ; Ekranda gorunecek Lux degeri (I??k artt?kça artar)
    
    ; LUX %100 iken PERDE %0 olmasi icin tersliyoruz
    MOVF    LDR_VAL, W
    SUBLW   D'100'          
    MOVWF   DESIRED_ST      ; Hedef konum (Isik arttikca duser)
    GOTO    KONTROL_ET

MANUEL_OKU
    MOVLW   B'10001001'
    MOVWF   ADCON0
    CALL    GECIKME_KISA
    CALL    ADC_OKU
    MOVF    ADRESH, W
    CALL    SCALE_POT_100   
    MOVWF   POT_VAL
    MOVWF   DESIRED_ST      

KONTROL_ET
    MOVF    DESIRED_ST, W
    XORWF   LAST_VAL, W
    BTFSS   STATUS, Z
    CALL    LCD_EKRAN_YAZ   
    MOVF    DESIRED_ST, W
    MOVWF   LAST_VAL        

    MOVF    CURRENT_ST, W
    XORWF   DESIRED_ST, W
    BTFSC   STATUS, Z       
    GOTO    ANA_DONGU

    MOVF    CURRENT_ST, W
    SUBWF   DESIRED_ST, W
    BTFSC   STATUS, C       
    GOTO    KAPAT_YOLU      
    GOTO    AC_YOLU         

AC_YOLU
    MOVLW   D'10'           
    MOVWF   STEP_LOOP
AC_L
    CALL    SINGLE_STEP_CW         
    DECFSZ  STEP_LOOP, F
    GOTO    AC_L
    DECF    CURRENT_ST, F   
    CALL    LCD_EKRAN_YAZ   
    GOTO    ANA_DONGU

KAPAT_YOLU
    MOVLW   D'10'           
    MOVWF   STEP_LOOP
KP_L
    CALL    SINGLE_STEP_CCW        
    DECFSZ  STEP_LOOP, F
    GOTO    KP_L
    INCF    CURRENT_ST, F   
    CALL    LCD_EKRAN_YAZ   
    GOTO    ANA_DONGU

; --- MOTOR ---
SINGLE_STEP_CW
    INCF    PHASE_STEP, F
    MOVF    PHASE_STEP, W
    ANDLW   0x03
    CALL    STEP_TABLE
    MOVWF   PORTB
    CALL    GECIKME
    RETURN

SINGLE_STEP_CCW
    DECF    PHASE_STEP, F
    MOVF    PHASE_STEP, W
    ANDLW   0x03
    CALL    STEP_TABLE
    MOVWF   PORTB
    CALL    GECIKME
    RETURN

STEP_TABLE
    ADDWF   PCL, F
    RETLW   B'0001'
    RETLW   B'0010'
    RETLW   B'0100'
    RETLW   B'1000'

; --- LCD ---
LCD_EKRAN_YAZ
    MOVLW   0x80
    CALL    LCD_KOMUT
    MOVLW   'M'
    CALL    LCD_VERI
    MOVLW   'O'
    CALL    LCD_VERI
    MOVLW   'D'
    CALL    LCD_VERI
    MOVLW   ' '
    CALL    LCD_VERI
    BTFSC   MOD_SWITCH
    GOTO    LCD_MAN_M
    MOVLW   'A'
    CALL    LCD_VERI
    MOVLW   'U'
    CALL    LCD_VERI
    MOVLW   'T'
    CALL    LCD_VERI
    MOVLW   'O'
    CALL    LCD_VERI
    GOTO    LCD_LINE2
LCD_MAN_M
    MOVLW   'M'
    CALL    LCD_VERI
    MOVLW   'A'
    CALL    LCD_VERI
    MOVLW   'N'
    CALL    LCD_VERI
    MOVLW   ' '
    CALL    LCD_VERI

LCD_LINE2
    MOVLW   0xC0
    CALL    LCD_KOMUT
    BTFSC   MOD_SWITCH
    GOTO    LCD_DES_YAZ
    MOVLW   'L'
    CALL    LCD_VERI
    MOVLW   'U'
    CALL    LCD_VERI
    MOVLW   'X'
    CALL    LCD_VERI
    GOTO    LCD_VAL_BAS
LCD_DES_YAZ
    MOVLW   'D'
    CALL    LCD_VERI
    MOVLW   'E'
    CALL    LCD_VERI
    MOVLW   'S'
    CALL    LCD_VERI

LCD_VAL_BAS
    MOVLW   ' '
    CALL    LCD_VERI
    
    ; Sol taraftaki deger (LDR_VAL veya DESIRED_ST)
    BTFSC   MOD_SWITCH
    MOVF    DESIRED_ST, W
    BTFSS   MOD_SWITCH
    MOVF    LDR_VAL, W
    MOVWF   BIN_SAYI
    CALL    SAYI_BAS_3DIGIT
    MOVLW   '%'
    CALL    LCD_VERI
    
    MOVLW   ' '
    CALL    LCD_VERI
    MOVLW   '-'
    CALL    LCD_VERI
    MOVLW   ' '
    CALL    LCD_VERI
    
    ; Sag taraftaki deger (Motorun konumu)
    MOVF    CURRENT_ST, W
    MOVWF   BIN_SAYI
    CALL    SAYI_BAS_3DIGIT
    MOVLW   '%'
    CALL    LCD_VERI
    RETURN

; --- YARDIMCI ---
SAYI_BAS_3DIGIT
    CALL    BIN_TO_BCD
    MOVF    YUZLER, W
    ADDLW   0x30
    CALL    LCD_VERI
    MOVF    ONLAR, W
    ADDLW   0x30
    CALL    LCD_VERI
    MOVF    BIRLER, W
    ADDLW   0x30
    CALL    LCD_VERI
    RETURN

BIN_TO_BCD
    CLRF    YUZLER
    CLRF    ONLAR
    MOVF    BIN_SAYI, W
    MOVWF   BIRLER
Y_C
    MOVLW   D'100'
    SUBWF   BIRLER, W
    BTFSS   STATUS, C
    GOTO    O_C
    MOVWF   BIRLER
    INCF    YUZLER, F
    GOTO    Y_C
O_C
    MOVLW   D'10'
    SUBWF   BIRLER, W
    BTFSS   STATUS, C
    RETURN
    MOVWF   BIRLER
    INCF    ONLAR, F
    GOTO    O_C

SCALE_POT_100
    MOVWF   TEMP_MATH
    CLRF    BIN_SAYI
P_L
    MOVLW   D'51'
    SUBWF   TEMP_MATH, F
    BTFSS   STATUS, C
    GOTO    P_E
    MOVLW   D'20'
    ADDWF   BIN_SAYI, F
    GOTO    P_L
P_E
    MOVF    BIN_SAYI, W
    RETURN

SCALE_LDR_100
    MOVWF   TEMP_MATH
    CLRF    BIN_SAYI
L_L
    MOVLW   D'25'
    SUBWF   TEMP_MATH, F
    BTFSS   STATUS, C
    GOTO    L_E
    MOVLW   D'10'
    ADDWF   BIN_SAYI, F
    GOTO    L_L
L_E
    MOVF    BIN_SAYI, W
    RETURN

ADC_OKU
    BSF     ADCON0, GO
W_D
    BTFSC   ADCON0, GO
    GOTO    W_D
    RETURN

LCD_INIT
    MOVLW   0x38
    CALL    LCD_KOMUT
    MOVLW   0x0C
    CALL    LCD_KOMUT
    MOVLW   0x01
    CALL    LCD_KOMUT
    RETURN

LCD_KOMUT
    MOVWF   PORTD
    BCF     RS
    BSF     EN
    NOP
    BCF     EN
    CALL    GECIKME
    RETURN

LCD_VERI
    MOVWF   PORTD
    BSF     RS
    BSF     EN
    NOP
    BCF     EN
    CALL    GECIKME
    RETURN

GECIKME_KISA
    MOVLW   D'50'
    MOVWF   SAYAC1
L_S
    DECFSZ  SAYAC1, F
    GOTO    L_S
    RETURN

GECIKME
    MOVLW   D'5'
    MOVWF   SAYAC1
LA
    MOVLW   D'255'
    MOVWF   SAYAC2
LB
    DECFSZ  SAYAC2, F
    GOTO    LB
    DECFSZ  SAYAC1, F
    GOTO    LA
    RETURN

    END