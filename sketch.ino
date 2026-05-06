#include <Arduino.h>
#include <U8g2lib.h>
#include <Wire.h>
#include "Arduino_RouterBridge.h"

U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE);

#define Y_BASE 32 

int estado = 0; 
float aperturaOjos = 20.0; 
bool cerrando = false;
bool pausadoCerrado = false; 
unsigned long tiempoInicioPausa = 0;
unsigned long tiempoSiguienteParpadeo = 0;

void set_estado(int nuevoEstado) {
  estado = nuevoEstado;
}

void dibujarBaymax() {
  // --- LÓGICA DE ANIMACIÓN (Sin cambios) ---
  if (millis() > tiempoSiguienteParpadeo && !cerrando && !pausadoCerrado && aperturaOjos >= 20.0) {
    cerrando = true;
  }

  if (cerrando) {
    aperturaOjos -= 2.5;
    if (aperturaOjos <= 2.0) {
      aperturaOjos = 2.0;
      cerrando = false;
      pausadoCerrado = true;
      tiempoInicioPausa = millis();
    }
  } 
  else if (pausadoCerrado) {
    if (millis() - tiempoInicioPausa > 300) pausadoCerrado = false;
  } 
  else if (aperturaOjos < 20.0) {
    aperturaOjos += 1.5;
    if (aperturaOjos >= 20.0) {
      aperturaOjos = 20.0;
      tiempoSiguienteParpadeo = millis() + random(2500, 5501);
    }
  }

  // --- DIBUJO "ANTI-ESTIRAMIENTO" ---
  int h = (int)aperturaOjos;
  if (h < 2) h = 2; // Altura mínima de 2px (una línea)
  
  // SOLUCIÓN AL ESTIRAMIENTO: 
  // El radio de la esquina (r) nunca puede ser mayor que la mitad de la altura (h/2).
  // Si h es 2, el radio será 1. Si h es 20, el radio será 8 (el máximo).
  int r = h / 2;
  if (r > 8) r = 8; 

  int y_pos = Y_BASE - (h / 2);

  u8g2.setDrawColor(1); 

  // Dibujamos los ojos con el radio dinámico 'r'
  u8g2.drawRBox(25, y_pos, 20, h, r); 
  u8g2.drawRBox(83, y_pos, 20, h, r);
  
  // Línea conectora
  u8g2.drawBox(35, Y_BASE - 1, 58, 2);
}

void dibujarPuntosDiagonales() {
  int x_base = 105;
  int y_base = 20;
  int paso = (millis() / 400) % 4;
  if (paso >= 1) u8g2.drawDisc(x_base, y_base, 2);
  if (paso >= 2) u8g2.drawDisc(x_base + 6, y_base - 6, 3);
  if (paso >= 3) u8g2.drawDisc(x_base + 12, y_base - 12, 4);
}

void setup() {
  u8g2.begin();
  randomSeed(analogRead(0));
  Bridge.begin();
  Bridge.provide("set_estado", set_estado);
  tiempoSiguienteParpadeo = millis() + 2000;
}

void loop() {
  u8g2.clearBuffer();
  dibujarBaymax();
  if (estado == 1) dibujarPuntosDiagonales();
  u8g2.sendBuffer();
  delay(20); 
}