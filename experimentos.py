# Experimentos del robot de limpieza: efecto del número de agentes (M1).
# Autor: Sebastián de Jesús Cruz Cruz. Matrícula: A01667857.
# Fecha de creación: 2026-11-04.

import os
from multiprocessing import Pool

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from robot_limpieza import Habitacion, ejecutarSimulacion

ANCHO = 6
ALTO = 6
PORCENTAJE_SUCIEDAD = 40.0
PASOS_MAXIMOS = 100
NUMEROS_AGENTES = (1, 3, 5)
NUMEROS_CONTROL = (1, 3, 5)
PASOS_CONTROL = 1000
SEMILLAS = tuple(range(1, 51))
CARPETA_RESULTADOS = "resultados"


# Ejecuta una configuración y resume sus métricas.
# Parámetro: configuracion, tupla (numeroAgentes, semilla, pasosMaximos).
# Retorno: tupla (fila de resumen, lista de porcentajes limpios por paso).
def ejecutarConfiguracion(configuracion):
	numeroAgentes, semilla, pasosMaximos = configuracion
	modelo = ejecutarSimulacion(ANCHO, ALTO, numeroAgentes,
								PORCENTAJE_SUCIEDAD, semilla, pasosMaximos)
	final = modelo.historial[-1]
	movimientosHasta = None
	if modelo.tiempoLimpieza is not None:
		movimientosHasta = modelo.historial[modelo.tiempoLimpieza]["movimientos"]
	fila = {
		"agentes": numeroAgentes,
		"semilla": semilla,
		"porcentajeInicialSucio": 100.0 * modelo.celdasInicialesSucias / (ANCHO * ALTO),
		"pasosEjecutados": modelo.pasos,
		"limpiezaTotal": modelo.tiempoLimpieza is not None,
		"tiempoLimpieza": modelo.tiempoLimpieza,
		"porcentajeLimpioFinal": final["porcentajeLimpio"],
		"movimientos": final["movimientos"],
		"movimientosHastaLimpieza": movimientosHasta
	}
	curva = [registro["porcentajeLimpio"] for registro in modelo.historial]
	return fila, curva


# Corre todas las configuraciones en paralelo.
# Parámetros: numerosAgentes, tupla de enteros; pasosMaximos, entero positivo.
# Retorno: tupla (DataFrame de resumen, DataFrame de curvas promedio por paso).
def correrExperimentos(numerosAgentes, pasosMaximos):
	configuraciones = [(n, s, pasosMaximos) for n in numerosAgentes for s in SEMILLAS]
	with Pool() as piscina:
		resultados = piscina.map(ejecutarConfiguracion, configuraciones, chunksize=4)
	resumen = pd.DataFrame([fila for fila, _ in resultados])
	curvas = pd.DataFrame({"agentes": [f["agentes"] for f, _ in resultados]})
	matrizCurvas = pd.DataFrame([curva for _, curva in resultados])
	matrizCurvas["agentes"] = curvas["agentes"]
	promedios = matrizCurvas.groupby("agentes").mean()
	return resumen, promedios


# Agrega las métricas por número de agentes.
# Parámetro: resumen, DataFrame con una fila por ejecución.
# Retorno: DataFrame con una fila por número de agentes.
def agregarMetricas(resumen):
	filas = []
	for numeroAgentes, grupo in resumen.groupby("agentes"):
		exitos = grupo[grupo["limpiezaTotal"]]
		filas.append({
			"agentes": numeroAgentes,
			"ejecuciones": len(grupo),
			"exitos": len(exitos),
			"tiempoMedio": exitos["tiempoLimpieza"].mean(),
			"tiempoMediana": exitos["tiempoLimpieza"].median(),
			"tiempoDesv": exitos["tiempoLimpieza"].std(),
			"limpioFinalMedio": grupo["porcentajeLimpioFinal"].mean(),
			"movimientosMedio": grupo["movimientos"].mean(),
			"movimientosDesv": grupo["movimientos"].std(),
			"movimientosPorRobot": grupo["movimientos"].mean() / numeroAgentes,
			"movimientosHastaLimpieza": exitos["movimientosHastaLimpieza"].mean(),
			"movimientosHastaDesv": exitos["movimientosHastaLimpieza"].std()
		})
	return pd.DataFrame(filas)


# Dibuja y guarda las gráficas principales del análisis.
# Parámetros: resumen, ejecuciones; agregado, métricas por agentes;
# promedios, curva promedio de limpieza por paso; control, métricas con
# horizonte largo para 1 a 3 robots.
# Retorno: ninguno. Guarda PNG en la carpeta de resultados.
def graficar(resumen, agregado, promedios, control):
	colores = plt.cm.viridis([0.85 * i / (len(NUMEROS_AGENTES) - 1) for i in range(len(NUMEROS_AGENTES))])

	figura, eje = plt.subplots(figsize=(6.5, 4))
	for color, (numeroAgentes, curva) in zip(colores, promedios.iterrows()):
		eje.plot(curva.values, color=color, label=str(numeroAgentes) + " robots")
	eje.axhline(100, color="gray", linestyle=":")
	eje.set_xlabel("Paso")
	eje.set_ylabel("% de celdas limpias (media de 50 semillas)")
	eje.set_title("Avance de la limpieza")
	eje.set_xlim(0, PASOS_MAXIMOS)
	eje.legend(fontsize=7, ncol=2, loc="lower right")
	eje.grid(alpha=0.3)
	figura.tight_layout()
	figura.savefig(os.path.join(CARPETA_RESULTADOS, "curvas_limpieza.png"), dpi=200)
	plt.close(figura)

	figura, ejes = plt.subplots(1, 2, figsize=(10, 4))
	datosTiempo = [resumen[(resumen["agentes"] == n) & resumen["limpiezaTotal"]]["tiempoLimpieza"]
				   for n in NUMEROS_AGENTES]
	ejes[0].boxplot(datosTiempo, tick_labels=[str(n) for n in NUMEROS_AGENTES])
	ejes[0].set_xlabel("Número de robots")
	ejes[0].set_ylabel("Primer paso con limpieza total")
	ejes[0].set_title("Tiempo hasta limpieza total (sólo éxitos)")
	ejes[0].grid(alpha=0.3)
	ejes[1].errorbar(agregado["agentes"], agregado["movimientosMedio"],
					 yerr=agregado["movimientosDesv"], marker="o", capsize=3,
					 color="#003366")
	ejes[1].set_xlabel("Número de robots")
	ejes[1].set_ylabel("Movimientos efectivos totales")
	ejes[1].set_title("Movimientos en " + str(PASOS_MAXIMOS) + " pasos (media ± desv.)")
	ejes[1].grid(alpha=0.3)
	figura.tight_layout()
	figura.savefig(os.path.join(CARPETA_RESULTADOS, "tiempo_movimientos.png"), dpi=200)
	plt.close(figura)

	figura, ejes = plt.subplots(1, 2, figsize=(10, 4))
	tiempos = agregado.set_index("agentes")["tiempoMedio"].copy()
	for numeroAgentes, fila in control.set_index("agentes").iterrows():
		tiempos[numeroAgentes] = fila["tiempoMedio"]
	ejes[0].plot(tiempos.index, tiempos.values, marker="o", color="#003366",
				 label="Tiempo medio observado")
	ejes[0].plot(tiempos.index, tiempos.iloc[0] / tiempos.index.values,
				 linestyle="--", color="gray", label="Speedup ideal (T1 / n)")
	ejes[0].set_xscale("log")
	ejes[0].set_yscale("log")
	ejes[0].set_xlabel("Número de robots (escala log)")
	ejes[0].set_ylabel("Tiempo medio hasta limpieza total (log)")
	ejes[0].set_title("Rendimientos decrecientes")
	ejes[0].legend()
	ejes[0].grid(alpha=0.3, which="both")
	esfuerzo = agregado.set_index("agentes")["movimientosHastaLimpieza"].copy()
	for numeroAgentes, fila in control.set_index("agentes").iterrows():
		esfuerzo[numeroAgentes] = fila["movimientosHastaLimpieza"]
	ejes[1].plot(esfuerzo.index, esfuerzo.values, marker="s", color="#B5651D")
	ejes[1].set_xlabel("Número de robots")
	ejes[1].set_ylabel("Movimientos hasta limpieza total")
	ejes[1].set_title("Esfuerzo total para terminar")
	ejes[1].grid(alpha=0.3)
	figura.tight_layout()
	figura.savefig(os.path.join(CARPETA_RESULTADOS, "speedup.png"), dpi=200)
	plt.close(figura)


# Guarda una figura con el estado inicial y final de una ejecución ejemplo.
# Parámetros: numeroAgentes, semilla; enteros.
# Retorno: ninguno. Guarda PNG en la carpeta de resultados.
def graficarEjemplo(numeroAgentes, semilla):
	modelo = Habitacion(ANCHO, ALTO, numeroAgentes, PORCENTAJE_SUCIEDAD, semilla)
	estados = [capturarEstado(modelo)]
	for _ in range(PASOS_MAXIMOS):
		modelo.step()
		if modelo.pasos in (10, 50):
			estados.append(capturarEstado(modelo))
	estados.append(capturarEstado(modelo))
	figura, ejes = plt.subplots(1, len(estados), figsize=(3.2 * len(estados), 3.4))
	for eje, estado in zip(ejes, estados):
		dibujarEstado(modelo, estado, eje)
	figura.tight_layout()
	figura.savefig(os.path.join(CARPETA_RESULTADOS, "ejemplo_estados.png"), dpi=200)
	plt.close(figura)


# Guarda una copia del estado para dibujarlo después.
# Parámetro: modelo, habitación con agentes y suciedad actual.
# Retorno: diccionario con paso, posiciones y suciedad.
def capturarEstado(modelo):
	return {
		"paso": modelo.pasos,
		"posiciones": [agente.posicion for agente in modelo.agents],
		"suciedad": set(modelo.celdasSucias)
	}


# Representa agentes y suciedad en una cuadrícula.
# Parámetros: modelo, dimensiones; estado, captura; eje, eje de Matplotlib.
# Retorno: ninguno.
def dibujarEstado(modelo, estado, eje):
	for posicionX, posicionY in estado["suciedad"]:
		eje.add_patch(plt.Rectangle((posicionX, posicionY), 1, 1,
									facecolor="sandybrown"))
	ocupacion = {}
	for posicion in estado["posiciones"]:
		ocupacion[posicion] = ocupacion.get(posicion, 0) + 1
	for (posicionX, posicionY), cantidad in ocupacion.items():
		eje.scatter(posicionX + 0.5, posicionY + 0.5, s=120, color="#003366")
		eje.text(posicionX + 0.5, posicionY + 0.5, str(cantidad),
				 ha="center", va="center", color="white", fontsize=6)
	eje.set_xlim(0, modelo.ancho)
	eje.set_ylim(0, modelo.alto)
	eje.set_aspect("equal")
	eje.grid(alpha=0.25)
	eje.set_title("Paso " + str(estado["paso"]), fontsize=9)


# Corre todo, guarda CSV y gráficas, e imprime la tabla agregada.
# Parámetros: ninguno.
# Retorno: ninguno.
def main():
	os.makedirs(CARPETA_RESULTADOS, exist_ok=True)
	resumen, promedios = correrExperimentos(NUMEROS_AGENTES, PASOS_MAXIMOS)
	agregado = agregarMetricas(resumen)
	resumenControl, _ = correrExperimentos(NUMEROS_CONTROL, PASOS_CONTROL)
	control = agregarMetricas(resumenControl)
	resumenControl.to_csv(os.path.join(CARPETA_RESULTADOS, "ejecuciones_control.csv"), index=False)
	control.to_csv(os.path.join(CARPETA_RESULTADOS, "agregado_control.csv"), index=False)
	resumen.to_csv(os.path.join(CARPETA_RESULTADOS, "ejecuciones.csv"), index=False)
	agregado.to_csv(os.path.join(CARPETA_RESULTADOS, "agregado.csv"), index=False)
	graficar(resumen, agregado, promedios, control)
	graficarEjemplo(3, 42)
	print(agregado.round(2).to_string(index=False))
	print("Control (horizonte largo):")
	print(control.round(2).to_string(index=False))


if __name__ == "__main__":
	main()
