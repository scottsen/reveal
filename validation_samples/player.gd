extends CharacterBody2D
## Player controller for a 2D platformer game
## Handles movement, jumping, and combat actions

# Signals
signal health_changed(new_health)
signal died()
signal damage_taken(amount)

# Export variables (visible in editor)
export var max_health: int = 100
export var move_speed: float = 200.0
export var jump_force: float = -400.0
export var gravity: float = 980.0

# Node references
onready var sprite = $AnimatedSprite
onready var collision = $CollisionShape2D
onready var damage_timer = $DamageTimer

# State variables
var health: int = max_health
var is_invincible: bool = false
var velocity: Vector2 = Vector2.ZERO
var is_grounded: bool = false

# Constants
const MAX_FALL_SPEED = 500.0
const ACCELERATION = 50.0
const FRICTION = 30.0


func _ready() -> void:
	"""Initialize the player."""
	health = max_health
	emit_signal("health_changed", health)
	_setup_animations()


func _physics_process(delta: float) -> void:
	"""Handle physics updates every frame."""
	_handle_input()
	_apply_gravity(delta)
	_apply_movement(delta)
	velocity = move_and_slide(velocity, Vector2.UP)
	_update_animation()


func _handle_input() -> void:
	"""Process player input."""
	# Horizontal movement
	var direction = Input.get_axis("ui_left", "ui_right")
	if direction != 0:
		velocity.x = move_toward(velocity.x, direction * move_speed, ACCELERATION)
	else:
		velocity.x = move_toward(velocity.x, 0, FRICTION)

	# Jump
	if Input.is_action_just_pressed("ui_up") and is_on_floor():
		velocity.y = jump_force

	# Attack
	if Input.is_action_just_pressed("attack"):
		_perform_attack()


func _apply_gravity(delta: float) -> void:
	"""Apply gravity to the player."""
	if not is_on_floor():
		velocity.y += gravity * delta
		velocity.y = min(velocity.y, MAX_FALL_SPEED)


func _apply_movement(delta: float) -> void:
	"""Apply movement calculations."""
	is_grounded = is_on_floor()


func _update_animation() -> void:
	"""Update sprite animation based on state."""
	if velocity.x != 0:
		sprite.play("run")
		sprite.flip_h = velocity.x < 0
	else:
		sprite.play("idle")

	if not is_grounded:
		sprite.play("jump")


func _setup_animations() -> void:
	"""Configure animation settings."""
	sprite.frames = load("res://assets/player_animations.tres")


func take_damage(amount: int) -> void:
	"""Handle taking damage.

	Args:
		amount: Amount of damage to take
	"""
	if is_invincible:
		return

	health -= amount
	health = max(0, health)
	emit_signal("health_changed", health)
	emit_signal("damage_taken", amount)

	if health <= 0:
		_die()
	else:
		_start_invincibility()


func heal(amount: int) -> void:
	"""Restore health.

	Args:
		amount: Amount of health to restore
	"""
	health += amount
	health = min(health, max_health)
	emit_signal("health_changed", health)


func _perform_attack() -> void:
	"""Execute attack action."""
	sprite.play("attack")
	# Attack logic here
	pass


func _start_invincibility() -> void:
	"""Start invincibility frames after taking damage."""
	is_invincible = true
	damage_timer.start()
	_flash_sprite()


func _flash_sprite() -> void:
	"""Make sprite flash to indicate invincibility."""
	sprite.modulate.a = 0.5


func _die() -> void:
	"""Handle player death."""
	sprite.play("death")
	set_physics_process(false)
	emit_signal("died")


func _on_DamageTimer_timeout() -> void:
	"""Called when invincibility period ends."""
	is_invincible = false
	sprite.modulate.a = 1.0


# Inner class for power-ups
class PowerUp:
	var name: String
	var duration: float
	var active: bool = false

	func activate() -> void:
		active = true

	func deactivate() -> void:
		active = false
