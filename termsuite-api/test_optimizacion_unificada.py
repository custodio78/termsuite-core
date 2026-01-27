#!/usr/bin/env python3
"""
Script para verificar que la optimización unificada funciona correctamente
"""

import requests
import json
import time
import asyncio
from pathlib import Path
import statistics

# Configuración
API_BASE = "http://localhost:7000"

def create_test_tmx_optimized():
    """Crear un TMX de prueba para medir rendimiento"""
    tmx_content = '''<?xml version="1.0" encoding="UTF-8"?>
<tmx version="1.4">
  <header>
    <prop type="x-filename">test_optimized.tmx</prop>
  </header>
  <body>
    <t