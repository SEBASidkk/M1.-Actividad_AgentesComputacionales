# Simulación de robots de limpieza reactivos (M1, TC2008B).
# Autor: Sebastián de Jesús Cruz Cruz. Matrícula: A01667857.
# Fecha de creación: 2026-11-04.

import mesa

DIRECCIONES = (
	(-1, -1), (0, -1), (1, -1),
	(-1, 0),           (1, 0),
	(-1, 1),  (0, 1),  (1, 1)
)


# Selecciona las posiciones inicialmente sucias.
# Parámetros: ancho y alto, enteros positivos; porcentajeSuciedad,
# porcentaje entre 0 y 100; generador, objeto random.Random.
# Retorno: conjunto de tuplas (x, y), sin posiciones repetidas.
def crearSuciedad(ancho, alto, porcentajeSuciedad, generador):
	posiciones = [(x, y) for x in range(ancho) for y in range(alto)]
	cantidadSucias = round(ancho * alto * porcentajeSuciedad / 100)

	return set(generador.sample(posiciones, cantidadSucias))


# Intenta mover un agente en una de ocho direcciones.
# Parámetro: agente, objeto con posicion, movimientos y model.
# Retorno: ninguno. Sólo cuenta cambios efectivos de posición.
def intentarMovimiento(agente):
	desplazamientoX, desplazamientoY = agente.model.random.choice(DIRECCIONES)
	posicionX, posicionY = agente.posicion
	nuevaX = posicionX + desplazamientoX
	nuevaY = posicionY + desplazamientoY
	dentroEspacio = (
		0 <= nuevaX < agente.model.ancho
		and 0 <= nuevaY < agente.model.alto
	)
	if dentroEspacio:
		agente.posicion = (nuevaX, nuevaY)
		agente.movimientos += 1


# Ejecuta una acción de limpieza o un intento de movimiento.
# Parámetro: robot, agente con posicion, movimientos y model.
# Retorno: ninguno. Modifica el agente o la suciedad de su modelo.
def actuarRobot(robot):
	if robot.posicion in robot.model.celdasSucias:
		robot.model.celdasSucias.remove(robot.posicion)
	else:
		intentarMovimiento(robot)


# Calcula el porcentaje actual de celdas limpias.
# Parámetros: ancho y alto, dimensiones; celdasSucias, conjunto de posiciones.
# Retorno: porcentaje de limpieza como número entre 0 y 100.
def calcularPorcentajeLimpio(ancho, alto, celdasSucias):
	celdasTotales = ancho * alto
	celdasLimpias = celdasTotales - len(celdasSucias)
	return 100.0 * celdasLimpias / celdasTotales


# Actualiza el primer paso en que se alcanza la limpieza total.
# Parámetros: celdasSucias, posiciones pendientes; pasoActual, entero;
# tiempoAnterior, primer paso registrado o None.
# Retorno: primer tiempo observado o None si no se ha alcanzado la limpieza.
def actualizarTiempoLimpieza(celdasSucias, pasoActual, tiempoAnterior):
	if len(celdasSucias) == 0 and tiempoAnterior is None:
		return pasoActual
	return tiempoAnterior


class RobotLimpieza(mesa.Agent):

	# Inicializa al robot en la celda de origen y lo registra en Mesa.
	# Parámetro: model, habitación a la que pertenece.
	# Retorno: ninguno.
	def __init__(self, model):
		super().__init__(model)
		self.posicion = (0, 0)
		self.movimientos = 0

	# Ejecuta la función de comportamiento del robot.
	# Parámetros: ninguno.
	# Retorno: ninguno.
	def step(self):
		actuarRobot(self)


class Habitacion(mesa.Model):

	# Crea la habitación, la suciedad y los robots.
	# Parámetros: ancho, alto y numeroAgentes, enteros positivos;
	# porcentajeSuciedad, valor entre 0 y 100; semilla, semilla aleatoria.
	# Retorno: ninguno.
	def __init__(self, ancho=6, alto=6, numeroAgentes=1,
				 porcentajeSuciedad=40.0, semilla=42):
		super().__init__(rng=semilla)
		if any(type(valor) is not int or valor < 1
			   for valor in (ancho, alto, numeroAgentes)):
			raise ValueError("Dimensiones y agentes deben ser enteros positivos.")
		if not 0.0 <= porcentajeSuciedad <= 100.0:
			raise ValueError("El porcentaje debe estar entre 0 y 100.")
		self.ancho = ancho
		self.alto = alto
		self.pasos = 0
		self.historial = []
		self.celdasSucias = crearSuciedad(ancho, alto, porcentajeSuciedad, self.random)
		self.celdasInicialesSucias = len(self.celdasSucias)
		self.tiempoLimpieza = actualizarTiempoLimpieza(self.celdasSucias, 0, None)
		for _ in range(numeroAgentes):
			RobotLimpieza(self)
		self.registrarDatos()

	# Activa todos los robots y registra el estado al terminar el paso.
	# Parámetros: ninguno.
	# Retorno: ninguno.
	def step(self):
		self.agents.shuffle_do("step")
		self.pasos += 1
		self.tiempoLimpieza = actualizarTiempoLimpieza(
			self.celdasSucias, self.pasos, self.tiempoLimpieza
		)
		self.registrarDatos()

	# Guarda métricas del estado actual.
	# Parámetros: ninguno.
	# Retorno: ninguno. Agrega una fila al historial.
	def registrarDatos(self):
		self.historial.append({
			"paso": self.pasos,
			"porcentajeLimpio": calcularPorcentajeLimpio(
				self.ancho, self.alto, self.celdasSucias
			),
			"movimientos": sum(robot.movimientos for robot in self.agents)
		})


# Ejecuta una simulación completa durante todo el horizonte.
# Parámetros: ancho, alto, numeroAgentes, porcentajeSuciedad, semilla, como
# en Habitacion; pasosMaximos, entero positivo con el tiempo máximo.
# Retorno: modelo ya ejecutado, con historial y tiempoLimpieza.
def ejecutarSimulacion(ancho, alto, numeroAgentes, porcentajeSuciedad,
					   semilla, pasosMaximos):
	modelo = Habitacion(ancho, alto, numeroAgentes, porcentajeSuciedad, semilla)
	for _ in range(pasosMaximos):
		modelo.step()
	return modelo
