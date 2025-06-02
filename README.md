# BCL - Blender Controller Link

**BCL (Blender Controller Link)** is a Blender add-on that lets you use a game controller or gamepad as a real-time input device inside Blender. It turns controller inputs into animatable properties that can drive bones, geometry nodes, object transforms, and more — enabling intuitive, physical control for animation, rig testing, live performances, and procedural systems.

## Features

- Real-time input from supported game controllers
- Maps axes and buttons to any property using drivers
- Control objects, rigs, and geometry nodes with physical input
- Record inputs directly as keyframes on the timeline
- No setup needed
- Lightweight, fast, and non-intrusive

## Installation

1. Download the ZIP of this repository.
2. In Blender, go to **Edit > Preferences > Add-ons**.
3. Click **Install...** and select the ZIP file.
4. Enable **Blender Controller Link (BCL)** in the list.

## Usage

- In the 3D Viewport, open the **BCL** panel in the right sidebar (N-panel).
- Press the **"Live Inputs"** button to start testing controller inputs.
- Press the **"Record Inputs"** button to start recording controller inputs.
- Right click one of the property in the addon panel > Copy as New Driver, and the right click the property that you want driven (an object X location for example) and Paste Driver.
- For use in Geometry Nodes, look for the BCL_ControllerInputs nodegroup under Group (Add Node)

## Requirements

- Blender 4.4 or newer


