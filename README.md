# Cartoon Wheel Setup Tool

**Version:** 1.0 (2026)  
**License:** MIT (Free for educational, personal and commercial projects. If you use it, a credit is always appreciated.)  
**Gumroad:** [Download for Free on Gumroad](https://yafarba.gumroad.com/l/cartoonwheeltool)

![Cartoon Wheel Setup Tool Demo](cartoon_wheel_setup_tool_demo.gif)

---

## 🛠️ Requirements

*   **Autodesk Maya:** 2022 / 2023 / 2024 / 2025 / 2026+ (Python 3)

---

## 📝 Description

This tool generates a fully procedural cartoon wheel rig directly from a selected polygon mesh. It builds an IK spline-based setup with controls, deformation clusters, and optional squash & stretch (flare deformer). 

The wheel keeps its custom shape while it rotates, so even deformed or non-circular wheels spin correctly without changing their silhouette. Perfect for cartoon animation setups (cars, robots, stylized rigs) and production pipelines.

---

## 🚀 Installation and Launch Instructions

### Option 1: Drag & Drop (Fastest)

*   Simply drag and drop the `cartoon_wheel_setup_tool.py` file directly into the Maya viewport.

### Option 2: Run via Maya Scripts Folder

1. Copy the `cartoon_wheel_setup_tool.py` file into your Maya scripts directory:
   * **Windows:** `Documents\maya\<version>\scripts\`
   * **macOS:** `/Users/<username>/Library/Preferences/Autodesk/maya/<version>/scripts/`
   * **Linux:** `~/maya/<version>/scripts/`

2. Open Maya, navigate to the **Script Editor**, and open a **PYTHON** tab.
3. Paste and execute the following code:

```python
import cartoon_wheel_setup_tool
cartoon_wheel_setup_tool.onMayaDroppedPythonFile()
```

4. *(Optional)* Highlight this code in the Script Editor and middle-mouse drag it onto your **Shelf** to create a quick-access button.

---

## 🛠️ How To Use

1. **Select your wheel geometry:** select the tire first, then select all rigid parts (rim, bolts, etc.) in your scene.
2. **Launch** the tool UI.
3. **Adjust settings:**
   * Joints Count
   * Curve Sections
   * Tire Radius
   * Squash & Stretch *(optional)*
4. Click the **"Create Rig"** button.
5. **Animate using:**
   * 🔴 **Red Main_CTRL:** global wheel movement
   * 🔄 **wheelRotate attribute:** wheel spinning
   * 🟡 **Yellow CV controls:** deformation shaping
