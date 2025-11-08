/**
 * Unified input manager for keyboard and gamepad controls
 * Converts raw inputs into standardized rover control commands
 * 
 * Supports multiple drive modes for 6-wheel independent drive/steer rover
 */

export type DriveMode = 'ackermann' | 'crab' | 'tank' | 'spin' | 'point-turn'

export interface RoverInputState {
  // Motor speeds for 6 wheels [-1.0 to 1.0]
  // Index: 0=FL, 1=FR, 2=ML, 3=MR, 4=RL, 5=RR
  motors: [number, number, number, number, number, number]
  
  // Steering angles for 6 wheels [0-180 degrees, 90=straight]
  // Index: 0=FL, 1=FR, 2=ML, 3=MR, 4=RL, 5=RR
  servos: [number, number, number, number, number, number]
  
  // Current drive mode
  driveMode: DriveMode
  
  // E-stop flag
  emergencyStop: boolean
}

export type InputCallback = (state: RoverInputState) => void

/**
 * Gamepad button/axis mapping for Xbox controllers
 */
const GAMEPAD_MAP = {
  // Axes
  LEFT_STICK_X: 0,
  LEFT_STICK_Y: 1,
  RIGHT_STICK_X: 2,
  RIGHT_STICK_Y: 3,
  
  // Buttons
  A: 0,
  B: 1,
  X: 2,
  Y: 3,
  LB: 4,
  RB: 5,
  LT: 6,
  RT: 7,
  BACK: 8,
  START: 9,
  LEFT_STICK_BUTTON: 10,
  RIGHT_STICK_BUTTON: 11,
  DPAD_UP: 12,
  DPAD_DOWN: 13,
  DPAD_LEFT: 14,
  DPAD_RIGHT: 15,
}

/**
 * Keyboard key mapping
 */
const KEY_MAP = {
  // Motor control
  FORWARD: ['w', 'ArrowUp'],
  BACKWARD: ['s', 'ArrowDown'],
  LEFT: ['a', 'ArrowLeft'],
  RIGHT: ['d', 'ArrowRight'],
  

// Driving style description
// Ackermann Steering - Traditional car-like steering (front wheels steer)
// Crab/Strafe - All wheels point same direction, move sideways
// Tank Drive - Left/right side differential (wheels pointed forward)
// Spin Turn - Wheels form a circle around center, rotate in place
// Point Turn - Front/rear steer opposite, pivot around middle wheels
// Custom - Any arbitrary wheel angle/speed combination
  // Drive mode switching
  MODE_ACKERMANN: ['1'],
  MODE_CRAB: ['2'],
  MODE_TANK: ['3'],
  MODE_SPIN: ['4'],
  MODE_POINT_TURN: ['5'],
  
  // Emergency stop
  ESTOP: [' ', 'Escape'],
}

export class InputManager {
  private state: RoverInputState
  private previousState: RoverInputState | null = null
  private callback: InputCallback | null = null
  private keyboardPressed: Set<string> = new Set()
  private gamepadIndex: number | null = null
  private animationFrameId: number | null = null
  private deadzone = 0.15 // Gamepad stick deadzone
  
  constructor() {
    // Initialize with neutral state
    this.state = {
      motors: [0, 0, 0, 0, 0, 0],
      servos: [90, 90, 90, 90, 90, 90], // Neutral position (straight)
      driveMode: 'ackermann', // Default to car-like steering
      emergencyStop: false,
    }
  }
  
  /**
   * Start listening for inputs
   */
  start(callback: InputCallback): void {
    this.callback = callback
    
    // Keyboard listeners
    window.addEventListener('keydown', this.handleKeyDown)
    window.addEventListener('keyup', this.handleKeyUp)
    
    // Gamepad listeners
    window.addEventListener('gamepadconnected', this.handleGamepadConnected)
    window.addEventListener('gamepaddisconnected', this.handleGamepadDisconnected)
    
    // Check for already-connected gamepads on start
    console.log('[InputManager] Starting... checking for gamepads')
    const gamepads = navigator.getGamepads()
    console.log('[InputManager] navigator.getGamepads() result:', gamepads)
    for (let i = 0; i < gamepads.length; i++) {
      if (gamepads[i]) {
        console.log(`[InputManager] Found pre-connected gamepad at index ${i}:`, gamepads[i]?.id)
        console.log('[InputManager] Note: You may need to press a button for it to become active')
      }
    }
    
    // Start polling loop
    this.pollInputs()
    
    console.log('[InputManager] Started successfully')
  }
  
  /**
   * Stop listening for inputs
   */
  stop(): void {
    window.removeEventListener('keydown', this.handleKeyDown)
    window.removeEventListener('keyup', this.handleKeyUp)
    window.removeEventListener('gamepadconnected', this.handleGamepadConnected)
    window.removeEventListener('gamepaddisconnected', this.handleGamepadDisconnected)
    
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId)
      this.animationFrameId = null
    }
    
    this.callback = null
    console.log('InputManager stopped')
  }
  
  /**
   * Keyboard event handlers
   */
  private handleKeyDown = (event: KeyboardEvent): void => {
    this.keyboardPressed.add(event.key)
    
    // Check for emergency stop
    if (KEY_MAP.ESTOP.includes(event.key)) {
      this.state.emergencyStop = true
      this.emitState()
    }
  }
  
  private handleKeyUp = (event: KeyboardEvent): void => {
    this.keyboardPressed.delete(event.key)
  }
  
  /**
   * Gamepad event handlers
   */
  private handleGamepadConnected = (event: GamepadEvent): void => {
    console.log('[InputManager] 🎮 Gamepad connected event fired!')
    console.log('[InputManager] Gamepad:', event.gamepad.id)
    console.log('[InputManager] Index:', event.gamepad.index)
    console.log('[InputManager] Buttons:', event.gamepad.buttons.length)
    console.log('[InputManager] Axes:', event.gamepad.axes.length)
    this.gamepadIndex = event.gamepad.index
  }
  
  private handleGamepadDisconnected = (event: GamepadEvent): void => {
    console.log('[InputManager] 🎮 Gamepad disconnected:', event.gamepad.id)
    if (this.gamepadIndex === event.gamepad.index) {
      this.gamepadIndex = null
    }
  }
  
  /**
   * Get current gamepad state
   */
  private getGamepad(): Gamepad | null {
    if (this.gamepadIndex === null) return null
    const gamepads = navigator.getGamepads()
    return gamepads[this.gamepadIndex] || null
  }
  
  /**
   * Apply deadzone to gamepad axis value
   */
  private applyDeadzone(value: number): number {
    return Math.abs(value) < this.deadzone ? 0 : value
  }
  
  /**
   * Clamp value to range
   */
  private clamp(value: number, min: number, max: number): number {
    return Math.max(min, Math.min(max, value))
  }
  
  /**
   * Round servo angle to integer (Pydantic expects int)
   */
  private roundServoAngle(angle: number): number {
    return Math.round(this.clamp(angle, 0, 180))
  }
  
  /**
   * Check if state has changed significantly
   */
  private hasStateChanged(): boolean {
    if (!this.previousState) return true
    
    // Check emergency stop
    if (this.state.emergencyStop !== this.previousState.emergencyStop) return true
    
    // Check drive mode
    if (this.state.driveMode !== this.previousState.driveMode) return true
    
    // Check motors (compare with small epsilon for floating point)
    for (let i = 0; i < 6; i++) {
      if (Math.abs(this.state.motors[i] - this.previousState.motors[i]) > 0.01) return true
    }
    
    // Check servos (integer comparison)
    for (let i = 0; i < 6; i++) {
      if (this.state.servos[i] !== this.previousState.servos[i]) return true
    }
    
    return false
  }
  
  /**
   * Update state from keyboard inputs
   */
  private updateFromKeyboard(): void {
    let forward = 0
    let turn = 0
    
    // Movement
    if (KEY_MAP.FORWARD.some(k => this.keyboardPressed.has(k))) forward += 1
    if (KEY_MAP.BACKWARD.some(k => this.keyboardPressed.has(k))) forward -= 1
    if (KEY_MAP.LEFT.some(k => this.keyboardPressed.has(k))) turn -= 1
    if (KEY_MAP.RIGHT.some(k => this.keyboardPressed.has(k))) turn += 1
    
    // Drive mode switching
    if (KEY_MAP.MODE_ACKERMANN.some(k => this.keyboardPressed.has(k))) {
      this.state.driveMode = 'ackermann'
    }
    if (KEY_MAP.MODE_CRAB.some(k => this.keyboardPressed.has(k))) {
      this.state.driveMode = 'crab'
    }
    if (KEY_MAP.MODE_TANK.some(k => this.keyboardPressed.has(k))) {
      this.state.driveMode = 'tank'
    }
    if (KEY_MAP.MODE_SPIN.some(k => this.keyboardPressed.has(k))) {
      this.state.driveMode = 'spin'
    }
    if (KEY_MAP.MODE_POINT_TURN.some(k => this.keyboardPressed.has(k))) {
      this.state.driveMode = 'point-turn'
    }
    
    // Apply drive mode kinematics
    this.applyDriveMode(forward, turn)
  }
  
  /**
   * Update state from gamepad inputs
   */
  private updateFromGamepad(gamepad: Gamepad): void {
    // Left stick: forward/backward (Y-axis inverted)
    const leftY = -this.applyDeadzone(gamepad.axes[GAMEPAD_MAP.LEFT_STICK_Y])
    
    // Right stick X: turning
    const rightX = this.applyDeadzone(gamepad.axes[GAMEPAD_MAP.RIGHT_STICK_X])
    
    // D-pad for drive mode switching
    if (gamepad.buttons[GAMEPAD_MAP.DPAD_UP]?.pressed) {
      this.state.driveMode = 'ackermann'
    }
    if (gamepad.buttons[GAMEPAD_MAP.DPAD_LEFT]?.pressed) {
      this.state.driveMode = 'crab'
    }
    if (gamepad.buttons[GAMEPAD_MAP.DPAD_DOWN]?.pressed) {
      this.state.driveMode = 'tank'
    }
    if (gamepad.buttons[GAMEPAD_MAP.DPAD_RIGHT]?.pressed) {
      this.state.driveMode = 'spin'
    }
    
    // Apply drive mode kinematics
    this.applyDriveMode(leftY, rightX)
    
    // Emergency stop: B button
    if (gamepad.buttons[GAMEPAD_MAP.B]?.pressed) {
      this.state.emergencyStop = true
    }
  }
  
  /**
   * Apply drive mode kinematics to convert forward/turn inputs to wheel speeds and angles
   */
  private applyDriveMode(forward: number, turn: number): void {
    // Wheel indices: 0=FL, 1=FR, 2=ML, 3=MR, 4=RL, 5=RR
    
    switch (this.state.driveMode) {
      case 'ackermann':
        // Front wheels steer, all wheels drive (car-like)
        this.applyAckermannSteering(forward, turn)
        break
      
      case 'crab':
        // All wheels point same direction, strafe sideways
        this.applyCrabSteering(forward, turn)
        break
      
      case 'tank':
        // All wheels straight, differential drive (left vs right)
        this.applyTankSteering(forward, turn)
        break
      
      case 'spin':
        // Wheels form circle, rotate in place
        this.applySpinSteering(turn)
        break
      
      case 'point-turn':
        // Front/rear steer opposite, pivot around middle
        this.applyPointTurnSteering(forward, turn)
        break
    }
  }
  
  /**
   * Ackermann steering - front wheels steer, car-like behavior
   */
  private applyAckermannSteering(forward: number, turn: number): void {
    // All wheels drive at same speed
    const speed = this.clamp(forward, -1, 1)
    this.state.motors = [speed, speed, speed, speed, speed, speed]
    
    // Front wheels steer, others straight
    const steerAngle = 90 + turn * 45 // ±45 degrees from center
    this.state.servos[0] = this.roundServoAngle(steerAngle) // FL
    this.state.servos[1] = this.roundServoAngle(steerAngle) // FR
    this.state.servos[2] = 90 // ML straight
    this.state.servos[3] = 90 // MR straight
    this.state.servos[4] = 90 // RL straight
    this.state.servos[5] = 90 // RR straight
  }
  
  /**
   * Crab/strafe - all wheels point same direction
   */
  private applyCrabSteering(forward: number, turn: number): void {
    // All wheels drive at same speed
    const speed = this.clamp(Math.sqrt(forward * forward + turn * turn), -1, 1)
    this.state.motors = [speed, speed, speed, speed, speed, speed]
    
    // All wheels point in direction of movement
    const angle = Math.atan2(turn, forward) * (180 / Math.PI)
    const steerAngle = this.roundServoAngle(90 + angle)
    this.state.servos = [steerAngle, steerAngle, steerAngle, steerAngle, steerAngle, steerAngle]
  }
  
  /**
   * Tank drive - all wheels straight, differential left/right
   */
  private applyTankSteering(forward: number, turn: number): void {
    // All wheels straight
    this.state.servos = [90, 90, 90, 90, 90, 90]
    
    // Differential drive
    const leftSpeed = this.clamp(forward + turn, -1, 1)
    const rightSpeed = this.clamp(forward - turn, -1, 1)
    
    this.state.motors[0] = leftSpeed  // FL
    this.state.motors[1] = rightSpeed // FR
    this.state.motors[2] = leftSpeed  // ML
    this.state.motors[3] = rightSpeed // MR
    this.state.motors[4] = leftSpeed  // RL
    this.state.motors[5] = rightSpeed // RR
  }
  
  /**
   * Spin turn - wheels form circle around center, rotate in place
   */
  private applySpinSteering(turn: number): void {
    const speed = Math.abs(turn)
    const direction = turn > 0 ? 1 : -1
    
    // Front left: steer right, drive forward
    this.state.servos[0] = 135 // 45° right
    this.state.motors[0] = speed * direction
    
    // Front right: steer left, drive forward
    this.state.servos[1] = 45 // 45° left
    this.state.motors[1] = speed * direction
    
    // Middle wheels: perpendicular to rover
    this.state.servos[2] = 180 // ML pointing right
    this.state.motors[2] = speed * direction
    this.state.servos[3] = 0   // MR pointing left
    this.state.motors[3] = speed * direction
    
    // Rear left: steer left, drive forward
    this.state.servos[4] = 45 // 45° left
    this.state.motors[4] = speed * direction
    
    // Rear right: steer right, drive forward
    this.state.servos[5] = 135 // 45° right
    this.state.motors[5] = speed * direction
  }
  
  /**
   * Point turn - front/rear steer opposite, pivot around middle wheels
   */
  private applyPointTurnSteering(forward: number, turn: number): void {
    // Middle wheels straight
    this.state.servos[2] = 90
    this.state.servos[3] = 90
    
    // Front wheels steer based on turn
    const frontSteer = 90 + turn * 45
    this.state.servos[0] = this.roundServoAngle(frontSteer)
    this.state.servos[1] = this.roundServoAngle(frontSteer)
    
    // Rear wheels steer opposite to front
    const rearSteer = 90 - turn * 45
    this.state.servos[4] = this.roundServoAngle(rearSteer)
    this.state.servos[5] = this.roundServoAngle(rearSteer)
    
    // All wheels drive at same speed
    const speed = this.clamp(forward, -1, 1)
    this.state.motors = [speed, speed, speed, speed, speed, speed]
  }
  
  /**
   * Main polling loop
   */
  private pollInputs = (): void => {
    // Reset emergency stop flag (needs to be re-triggered each frame)
    this.state.emergencyStop = false
    
    // Get gamepad state (with fallback detection)
    let gamepad = this.getGamepad()
    
    // If no gamepad but we haven't checked recently, scan for gamepads
    // This handles browsers that don't fire gamepadconnected events
    if (!gamepad && this.gamepadIndex === null) {
      const gamepads = navigator.getGamepads()
      for (let i = 0; i < gamepads.length; i++) {
        const foundGamepad = gamepads[i]
        if (foundGamepad) {
          this.gamepadIndex = i
          gamepad = foundGamepad
          console.log('Gamepad auto-detected:', foundGamepad.id)
          break
        }
      }
    }
    
    if (gamepad) {
      // Gamepad has priority over keyboard
      this.updateFromGamepad(gamepad)
    } else {
      // Fall back to keyboard
      this.updateFromKeyboard()
    }
    
    // Only emit state if it has changed (reduces network spam)
    if (this.hasStateChanged()) {
      this.emitState()
      // Save current state for next comparison
      this.previousState = { ...this.state }
    }
    
    // Continue polling
    this.animationFrameId = requestAnimationFrame(this.pollInputs)
  }
  
  /**
   * Emit current state to callback
   */
  private emitState(): void {
    if (this.callback) {
      this.callback({ ...this.state })
    }
  }
  
  /**
   * Get current gamepad connection status
   * Scans all gamepad slots to handle browsers that don't fire connection events
   */
  isGamepadConnected(): boolean {
    // First check if we have a known gamepad index
    if (this.gamepadIndex !== null && this.getGamepad() !== null) {
      return true
    }
    
    // Fallback: scan all gamepad slots for connected gamepads
    // This handles browsers that don't fire gamepadconnected events reliably
    const gamepads = navigator.getGamepads()
    for (let i = 0; i < gamepads.length; i++) {
      if (gamepads[i]) {
        // Found a connected gamepad - remember its index
        this.gamepadIndex = i
        console.log('Gamepad detected via polling:', gamepads[i]?.id)
        return true
      }
    }
    
    return false
  }
  
  /**
   * Get current state (for debugging/display)
   */
  getState(): RoverInputState {
    return { ...this.state }
  }
  
  /**
   * Get current drive mode
   */
  getDriveMode(): DriveMode {
    return this.state.driveMode
  }
  
  /**
   * Set drive mode manually
   */
  setDriveMode(mode: DriveMode): void {
    this.state.driveMode = mode
    this.emitState()
  }
}
