#!/usr/bin/env python3
import math
import time
import os

def is_land(lat, lon):
    """Simple, clear continent detection - LAND ONLY"""
    # Normalize longitude to -180 to 180
    lon = ((lon + 180) % 360) - 180
    
    # CLEAR LAND REGIONS - simple bounding boxes
    
    # North America
    if -130 < lon < -60 and 15 < lat < 75:
        return True
    
    # Central America & Caribbean
    if -100 < lon < -60 and 8 < lat < 20:
        return True
    
    # South America
    if -82 < lon < -35 and -56 < lat < 13:
        return True
    
    # Greenland
    if -75 < lon < -10 and 60 < lat < 85:
        return True
    
    # Western Europe & UK
    if -15 < lon < 30 and 40 < lat < 72:
        return True
    
    # Africa
    if -20 < lon < 55 and -35 < lat < 38:
        return True
    
    # Middle East
    if 25 < lon < 65 and 12 < lat < 42:
        return True
    
    # Central Asia
    if 45 < lon < 100 and 35 < lat < 60:
        return True
    
    # South Asia (India, Pakistan, Bangladesh)
    if 65 < lon < 100 and 5 < lat < 37:
        return True
    
    # East Asia (China)
    if 73 < lon < 135 and 15 < lat < 55:
        return True
    
    # Southeast Asia
    if 95 < lon < 145 and -10 < lat < 25:
        return True
    
    # Japan & Korea
    if 125 < lon < 147 and 28 < lat < 50:
        return True
    
    # Russia (Northern Eurasia)
    if 19 < lon < 180 and 50 < lat < 81:
        return True
    
    # Australia
    if 113 < lon < 155 and -45 < lat < -10:
        return True
    
    # New Zealand
    if 166 < lon < 179 and -47 < lat < -34:
        return True
    
    # Indonesia
    if 95 < lon < 142 and -11 < lat < 7:
        return True
    
    # Papua New Guinea
    if 140 < lon < 155 and -13 < lat < 0:
        return True
    
    return False

def create_globe(rotation_angle):
    """Generate a 3D rotating numeric globe - DIGITS ON LAND ONLY"""
    # Use a height that fits well on most terminals without scrolling
    width, height = 140, 36
    canvas = [[' ' for _ in range(width)] for _ in range(height)]
    
    center_x = width // 2
    center_y = height // 2
    # Radius in character width units
    radius = 32
    
    # Aspect ratio adjustment (characters are typically ~2x taller than wide)
    aspect_ratio = 0.5
    
    # Step through each screen position
    for screen_y in range(height):
        for screen_x in range(width):
            # Convert screen coordinates to normalized 2D circle
            dx = (screen_x - center_x) / radius
            dy = (screen_y - center_y) / (radius * aspect_ratio)
            
            # Check if point falls within sphere bounds
            dist_sq = dx * dx + dy * dy
            if dist_sq > 1.0:
                continue
            
            # Calculate z depth on sphere surface
            z_depth = math.sqrt(1.0 - dist_sq)
            
            # Skip points too close to edge for smoother appearance
            if z_depth < 0.15:
                continue
            
            # 3D rotation around Y axis for smooth globe rotation
            rotated_x = dx * math.cos(rotation_angle) - z_depth * math.sin(rotation_angle)
            rotated_z = dx * math.sin(rotation_angle) + z_depth * math.cos(rotation_angle)
            
            # Convert 3D coordinates to latitude/longitude
            lat = math.degrees(math.asin(dy))
            lon = math.degrees(math.atan2(rotated_x, rotated_z))
            
            # LAND = show digits, OCEAN = show nothing (space)
            if is_land(lat, lon):
                # Show digits on land
                digit = str((int(lon * 0.5) + int(lat * 0.8)) % 10)
                canvas[screen_y][screen_x] = digit
            # else: keep as space (empty)
    
    return canvas

def render_canvas(canvas):
    """Render canvas with color"""
    output = []
    for row in canvas:
        line = ''.join(row)
        # Add ANSI color codes for ISU blue
        colored = '\033[36m' + line + '\033[0m'  # Cyan for ISU blue
        output.append(colored)
    return '\n'.join(output)

def main():
    """Main animation loop - refined globe with clear continents"""
    rotation = 0.0
    frame_count = 0
    
    try:
        while True:
            # Clear screen with pure cls/clear instead of just ANSI to prevent scrolling issues
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # Header with branding
            print("\033[1;36m🌍 ISU ISU ISU Global Sphere Recreation 🌍\033[0m")
            print("\033[36m" + "=" * 140 + "\033[0m")
            
            # Generate and render globe
            globe = create_globe(rotation)
            print(render_canvas(globe))
            
            # Footer
            print("\033[36m" + "=" * 140 + "\033[0m")
            print(f"\033[36mFrame: {frame_count:04d} | Rotation: {rotation:.3f} rad | Ctrl+C to stop\033[0m")
            
            # Increment rotation for smooth animation
            rotation += 0.15
            if rotation > 2 * math.pi:
                rotation -= 2 * math.pi
            
            frame_count += 1
            time.sleep(0.08)
            
    except KeyboardInterrupt:
        print("\n\n\033[1;32m✓ ISU Globe deactivated. Mission complete!\033[0m")

if __name__ == '__main__':
    main()
