# UI BASE.PDF COMPLETE SPECIFICATION
## Exact Aesthetic and Functional Requirements Extracted from 13 Pages

**Date:** January 5, 2026
**Source:** UI Base.pdf (13 pages)
**Purpose:** Complete specification for LightSpeed UI implementation

---

## GLOBAL AESTHETIC SYSTEM

### Color Palette (Exact Codes)

**Background:**
- Base: Deep blue gradient (#000033 → #0000ff)
- Cosmic depth effect with radial gradient from center
- Darker at edges, lighter in center
- NO black backgrounds anywhere

**Primary Accents:**
- **Cyan/Teal**: #00ffff, #00d4ff, #00ccff
  - Used for: Panel borders, highlights, grid lines
  - Border width: 2-3px
  - Glow effect on interactive elements

- **Magenta/Pink**: #ff1493, #ff00cc, #ff0080
  - Used for: Achilles sphere, glowing "+" icons
  - Pulsing animation effect
  - Radial gradient for glow

- **Green**: #00ff00, #00ff88, #00ffcc
  - Used for: Breadcrumbs, success indicators, "Go" buttons
  - Text with glow effect
  - Action buttons in radial menu

**Panel Colors:**
- Glass morphism: rgba(0, 20, 60, 0.7) - semi-transparent dark blue
- Border: Cyan #00d4ff at 2-3px
- Rounded corners: 15-20px radius
- Subtle shadow: 0 4px 12px rgba(0, 0, 0, 0.5)

**Company Branding:**
- **EMASSC**:
  - Background: Red-orange starfield with rainbow gradient sphere
  - Sphere colors: Rainbow spectrum (red→orange→yellow→green→blue→purple)
  - Text: Metallic rainbow gradient

- **Römer Industries**:
  - Background: Teal/cyan (#006666 → #008888)
  - Logo: Gold orbital design (#d4af37, #f0e68c)
  - Text: Gold with slight glow

---

### Typography System

**Font Families:**

1. **Headers/Titles**: Garamond (serif) or similar elegant serif
   - Used for: Page titles, section headers, "Achilles Assist"
   - Weight: Normal to Bold
   - Color: White (#ffffff) with slight cyan glow

2. **Body Text**: Arial, Helvetica, or clean sans-serif
   - Used for: Instructions, descriptions, menu items
   - Weight: Normal
   - Color: White (#ffffff) or light gray (#cccccc)

3. **Monospace/Code**: Consolas, Courier New
   - Used for: Breadcrumbs, technical data, file paths
   - Weight: Normal
   - Color: Green (#00ff88) for breadcrumbs, cyan for data

4. **Interactive Elements**: Sans-serif bold
   - Used for: Button labels, menu options
   - Weight: Bold
   - Color: White with appropriate accent color

**Font Sizes:**
- Page titles: 32-48px
- Section headers: 24-32px
- Body text: 14-16px
- Small labels: 12-14px
- Breadcrumbs: 18-20px

**Text Effects:**
- Subtle glow/shadow for readability against blue background
- Green text always has slight glow effect
- Headers use light text shadow: 0 2px 4px rgba(0, 0, 0, 0.8)

---

### Visual Effects Library

**1. Glass Morphism**
- Semi-transparent panels: opacity 0.6-0.8
- Backdrop blur: 10-15px (if supported)
- Border: 2-3px cyan (#00d4ff)
- Rounded corners: 15-20px
- Shadow depth: 0 4px 12px rgba(0, 0, 0, 0.5)

**2. Glowing "+" Icon**
- Center: Light gray/white cross (#cccccc)
- Inner glow: Magenta (#ff1493) radial gradient
- Outer glow: Softer magenta fade
- Size: 80-120px
- Animation: Subtle pulse (scale 1.0 → 1.05 → 1.0, 2s loop)

**3. Pulsing Achilles Sphere**
- Base: Magenta/pink gradient sphere (#ff1493 → #ff00cc)
- Rim: White/silver border (#ffffff, #cccccc)
- Striped pattern: Diagonal white stripes (optional)
- Glow: Magenta radial glow extending 20-30px
- Animation: Pulse opacity 0.8 → 1.0 → 0.8, 2-3s loop
- Microphone icon: White (#ffffff) centered

**4. Rounded Corners**
- All panels: 15-20px border-radius
- Buttons: 25-30px (pill shape)
- Cards: 20-25px
- Small elements: 8-12px

**5. Stacked Pages Effect** (Page 5)
- 3 layers visible
- Each layer offset by 5-8px (top-left)
- Each layer slightly darker/more transparent
- Shadow between layers: 2px 2px 4px rgba(0, 0, 0, 0.3)
- Creates depth perception

**6. Breadcrumb Style**
- Format: ">Category > Subcategory > Item"
- Color: Green (#00ff88)
- Font: Monospace
- Size: 18-20px
- Glow: Slight green glow effect
- Always at top of page

**7. Cyan Grid (Page 9 - 3D Visualization)**
- Grid color: Cyan (#00ffff)
- Grid spacing: Regular squares
- 3D perspective: Vanishing point at horizon
- Curvature: Grid warps around gravity wells (black holes)
- Gradient: Brighter in foreground, darker in background

**8. File Stack Icon**
- 3-4 page shapes stacked
- Each page offset by 3-5px
- White/light gray color
- Small shadow between pages
- Used to represent document attachments

---

## PAGE-BY-PAGE SPECIFICATIONS

### Pages 1-3: Action Cards Layout

**Layout Structure:**
```
┌─────────────────────────────────────────────────────────┐
│  [Left Sidebar]           [Action Cards 2-column]       │
│  Achilles Assist          [Card 1]    [Card 2]          │
│  - Welcome                                              │
│  - Instructions           (Pages 1-3 show different     │
│  - Input field            variations of cards)          │
│                                                         │
│  [Bottom Input]           Top-right: Settings icons     │
│  Response/Input Fields    (Enter, Profile, Gear)        │
└─────────────────────────────────────────────────────────┘
```

**Left Sidebar: "Achilles Assist"**
- Dimensions: ~25% screen width, full height
- Position: Fixed left
- Background: Glass morphism panel
- Border: Cyan 2px, rounded 15px
- Padding: 20-30px

**Content:**
1. **Title**: "Achilles Assist"
   - Font: Garamond/serif
   - Size: 28-32px
   - Color: White
   - Underline: Cyan

2. **Welcome Section**:
   - "Welcome Message:" (green)
   - "AI self introduction" (green)
   - "What to expect" (green)

3. **Instructions Section**:
   - "Instructions begin" (green)
   - Nested indicators: >, >>, >>>, > (green)

4. **Input Prompt**:
   - "Please Input;" (green)
   - "x, y, z" (green, monospace)

5. **Additional** (Page 4):
   - "How to;" (green)
   - "....." (green dots)

**Vertical Scrollbar** (Pages 1-3):
- Position: Between sidebar and main area
- Style: Thin white line with green slider dot
- Interactive slider

**Bottom Input Panel**:
- Width: Matches sidebar
- Background: Glass morphism
- Border: Cyan 2px
- Label: "Response / Input Fields" or "Response / Ask / Input Fields" (green)
- "Add Files" button: White "+" icon with black background, pill shape

**Action Cards** (Main Area):
- Layout: 2-column grid
- Card size: Large, ~40-45% screen width each
- Gap between cards: 30-40px
- Position: Centered in remaining space

**Individual Card:**
- Background: Gradient from gray (#555555) to dark blue-gray (#3a3a5a)
- Border: Rounded 25-30px
- Glow: Subtle outer glow matching card color (pink/magenta or blue)
- Center: Glowing "+" icon
- Text: White, centered above or on "+" icon
- Font: Garamond/serif for title
- Size: 24-32px

**Card Variations:**
- Page 1: "ADD Company" (pink glow) + "ADD Primary User" (blue glow)
- Page 2: "New User" (pink glow, centered)
- Page 3: "ADD Project" (pink glow, centered)
- Page 4: "ADD File" (pink glow) + "ADD Sub-Project" (blue glow)

**Top-Right Icons** (All pages):
1. Enter/Return icon (arrow in rounded square)
2. Profile/Globe icon (circular, white dots) - appears on pages 2+
3. Settings gear icon
- All icons: White, ~40px, with subtle glow

---

### Page 5: Document Viewer with Stacked Pages

**Layout:**
```
┌────────────────────────────────────────────────────────┐
│  >Business > Project Title > ...                       │
│                                                        │
│  [Stacked Document]              [ADD File Card]       │
│   ┌─3rd layer                                         │
│   │┌─2nd layer                                        │
│   ││┌─Document─────┐                                  │
│   │││ Title        │                                  │
│   │││ [Page icon]  │                                  │
│   │││ Content...   │                                  │
│   │││              │                                  │
│   │││ Notes:       │                                  │
│   │││ ...          │                                  │
│   ││└──────────────┘                                  │
│                                                        │
│                    Ask Achilles (mic icon)            │
└────────────────────────────────────────────────────────┘
```

**Breadcrumb Navigation:**
- Position: Top-left
- Format: ">Business > Project Title > ..."
- Color: Green (#00ff88)
- Font: Monospace (Consolas)
- Size: 18-20px
- Glow: Slight green glow

**Stacked Document Display:**
- 3 visible layers (pages stacked)
- Each layer: Offset 5-8px top-left from previous
- Colors: Front (lightest), middle (medium), back (darkest)
- Front layer shows document content
- Glass morphism panels for each layer
- Cyan border on front layer

**Document Content Panel:**
- Title bar: White background, "Document Title" in black
- Page preview: White background with blue text lines and green dots (mockup)
- Scroll bar: Green vertical slider on right
- Tool icons on right: Frame, edit, refresh, download (gray icons)
- Notes section: White panel at bottom with asterisk bullet points

**"ADD File" Card:**
- Same style as previous pages
- Pink/magenta glow
- Glowing "+" icon
- Text: "ADD File" in white

**Bottom "Ask Achilles":**
- Position: Bottom-center
- Microphone icon: Blue (#0080ff)
- Text: "Ask Achilles" in cyan/blue
- Glow effect around icon

**Top-Right Icons:**
- Consistent with previous pages
- Enter, Profile, Settings

---

### Page 6: Company Branding Display

**Layout:**
```
┌────────────────────────────────────────────────────────┐
│                                                        │
│  ┌─────────────────────┬──────────────────────────┐   │
│  │                     │                          │   │
│  │     EMASSC          │   RÖMER INDUSTRIES       │   │
│  │   (Rainbow Sphere)  │   (Gold Orbital Logo)    │   │
│  │                     │                          │   │
│  └─────────────────────┴──────────────────────────┘   │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**EMASSC Panel** (Left):
- Background: Red-orange starfield space scene
- Sphere: Large orange-to-yellow gradient sphere (sun-like)
- Rainbow effect: Magenta, green, blue light rays emanating from sphere
- Text: "EMASSC" in metallic rainbow gradient
- Subtitle: "Electromagnetic Mining Assets Space Strategy & Chaingraph" (small, white)
- Overall feel: Vibrant, energetic, rainbow spectrum

**Römer Industries Panel** (Right):
- Background: Solid teal/cyan (#006666 to #008888)
- Logo: Gold orbital swirl design (represents asteroid belt/orbital mechanics)
- Text: "RÖMER INDUSTRIES" in gold (#d4af37)
- Overall feel: Professional, corporate, space industry

**Panel Division:**
- Clean 50/50 split
- No border between panels (seamless)
- Each panel full height of display area

**Purpose:**
- Company selection/branding display
- Shows dual-company support (EMASSC and Römer)
- Central sphere in UI changes based on selected company

---

### Pages 7-8: Collapsible Menu System with Central Sphere

**Layout:**
```
┌────────────────────────────────────────────────────────┐
│  [Menu 1 Panel]        [Central         [Menu 4 Panel] │
│   - Option 1            Sphere]          - Option 1    │
│   - Option 2            + 4 Title        - Option 2    │
│   - Sub Options         Cards]           - Sub Options │
│                                                        │
│  [Company Logo]                                        │
│  (Bottom-left)         Ask Achilles                    │
└────────────────────────────────────────────────────────┘
```

**Menu Panels** (Left and Right):
- Position: Left side (Menu 1), Right side (Menu 4)
- Background: Glass morphism with cyan border
- Rounded corners: 15-20px
- Size: ~25-30% screen width each

**Menu Structure:**
- **Header**: "Menu 1" or "Menu 4" (underlined, white, Garamond)
- **Options**:
  - "Option 1", "Option 2", "Option 3" (white, underlined)
  - "Option 4 (Selected)" - marked as selected
- **Sub-options** (when expanded):
  - Indented: "__Sub Option 1", "__Sub Option 2", "__Sub Option 3"
  - Each with "Blurb" in cyan below
- **Selected indicator**: "(Selected)" in cyan or white

**Central Sphere:**
- **Page 7**: EMASSC orange/rainbow gradient sphere
- **Page 8**: Römer Industries teal/gold sphere
- Size: Large, ~200-250px diameter
- Glow: Matches company color (orange or teal)
- Company name visible on sphere
- Pulsing animation

**Title Cards** (Around Sphere):
- 4 small rectangular cards positioned around sphere
- Each labeled "Title" or "Selected"
- Rounded corners
- Cyan border
- Arrow icon in top-right corner
- Background: Transparent or dark

**Bottom-Left Company Logo:**
- **Page 7**: Römer Industries (teal background, gold logo, small square)
- **Page 8**: EMASSC (rainbow sphere, small square)
- Back arrow icon (< in circle)
- Purpose: Switch between companies

**Bottom-Center "Ask Achilles":**
- Microphone icon (blue)
- Text: "Ask Achilles" (cyan)
- Consistent with other pages

**Top-Right Icons:**
- Consistent set: Enter, Profile, Settings

**Interaction Pattern:**
- Menus expand/collapse to show sub-options
- Central sphere changes color based on selected company
- Title cards likely launch related functions

---

### Page 9: 3D Gravity Well Visualization (Physics)

**Layout:**
```
┌────────────────────────────────────────────────────────┐
│  >PY File Name / Business /              Ask Achilles  │
│                                          [Menu Panel]  │
│  ┌─────────────────────────────────┐    - Options     │
│  │                                 │                  │
│  │   3D CYAN GRID                  │    - Sub Opts    │
│  │   BLACK HOLES                   │                  │
│  │   (Gravity Well Visual)         │                  │
│  │                                 │                  │
│  └─────────────────────────────────┘                  │
│                                                        │
│  Graph/Render Title                                    │
│  Live Information about the graph... (3 columns)       │
└────────────────────────────────────────────────────────┘
```

**Breadcrumb:**
- ">PY File Name / Business /" (green, monospace)
- Top-left position

**3D Visualization Panel** (Main - Left side):
- Large rectangular panel (60-70% width)
- Background: Deep blue to black gradient
- Border: Cyan rounded 20px
- Content: **Cyan 3D grid with black holes**

**Cyan Grid Details:**
- Color: Bright cyan (#00ffff)
- Style: Perspective 3D grid squares
- Vanishing point: At horizon line
- Curvature: Grid warps downward around black holes
- Gradient: Brighter in foreground, darker at horizon
- Effect: Looks like rubber sheet with gravity wells

**Black Holes:**
- 2 black spheres of different sizes
- Positioned on grid surface
- Grid curves down around them (gravity well effect)
- Largest in foreground, smaller in background
- Pure black (#000000) with slight edge highlight

**Side Panel Tools** (Right of visualization):
- Frame/fullscreen icon (top)
- List/menu icon (middle)
- Refresh/reload icon
- Download icon (bottom)
- All icons: White, simple, vertical stack
- Background: Transparent or dark

**Menu Panel** (Top-Right):
- Standard collapsible menu
- Same style as Pages 7-8
- Options with sub-options and blurbs
- Cyan border, glass morphism

**Information Panel** (Bottom):
- Title: "Graph/Render Title" (white, Garamond)
- Background: Glass morphism panel, full width
- Border: Cyan rounded
- Content: "Live Information about the graph..." repeated
- Layout: 3 columns of text
- Text color: Green and cyan mixed
- Provides real-time data about visualization

**Top-Right Controls:**
- "Ask Achilles" (mic icon, top-right)
- Settings gear (bottom-right)
- Profile icon

**Purpose:**
- Embedded physics visualization (gravity wells, spacetime curvature)
- Real-time data display
- Interactive 3D rendering within UI

---

### Page 10: Dual-Page Document Viewer

**Layout:**
```
┌────────────────────────────────────────────────────────┐
│  >Doc File Name / Business /              Ask Achilles │
│                                           [Menu Panel] │
│  ┌──────────┬──────────┐                               │
│  │  Page 1  │  Page 2  │                               │
│  │  [Doc]   │  [Doc]   │                  [Author]     │
│  │  Content │  Content │                  [Info Panel] │
│  │          │          │                               │
│  └──────────┴──────────┘                               │
│  ┌──────────┬──────────┐                               │
│  │Foot Notes│AI Search │                               │
│  └──────────┴──────────┘         Page 1  ⭕  Page 2    │
└────────────────────────────────────────────────────────┘
```

**Breadcrumb:**
- ">Doc File Name / Business /" (green, monospace)
- Top-left

**Dual-Page Document Display:**
- 2 pages side-by-side
- Each page: White background (#ffffff)
- Content: Blue text lines (mockup)
- Border: Cyan rounded 15px on each page
- Spacing: ~20px gap between pages
- Size: Each page ~35-40% screen width

**Document Content Mockup:**
- Blue horizontal lines (headers)
- Light blue boxes (content blocks)
- Cyan bullet points
- Professional document layout

**Right Side Tools:**
- Frame icon (top)
- List icon
- Refresh icon
- Download icon (bottom)
- Vertical stack, white icons

**Foot Notes Panel** (Bottom-Left):
- Label: "Foot Notes;" (green)
- Content: Dotted text (mockup)
- Background: Dark glass morphism
- Border: Cyan
- Green text for footnote markers

**AI API Search Panel** (Bottom-Right):
- Label: "AI API Search;" (cyan/blue)
- Content: "Returned Results ...." (cyan/blue text)
- Background: Dark glass morphism
- Border: Cyan
- Shows AI-powered search results

**Author Info Panel** (Right Side):
- **Title**: "Author Name" (white, Garamond)
- **Subtitle**: "Notes about the document for reference ..." (cyan)
- **Section**: "Live Information about the History;" (green)
- **Metadata**: "Uploaded / Edited | __Who___ | __/__/20__" (cyan)
- Background: Glass morphism
- Border: Cyan rounded

**Page Navigation** (Bottom-Center):
- Circle indicator with "Page" label inside
- Number "1" on left (green)
- Number "2" on right (white)
- Shows current page position

**Menu Panel** (Top-Right):
- Standard collapsible menu
- Options with sub-options
- Consistent style

**Purpose:**
- Side-by-side document reading
- Foot notes + AI search integration
- Author/metadata tracking
- Professional document management

---

### Page 11: Dashboard with 4 Quadrants

**Layout:**
```
┌────────────────────────────────────────────────────────┐
│  User Name  ;  Position                                │
│                                                        │
│  ┌─────────────────┐        ┌──────────────────┐      │
│  │ Current         │        │ Quick Links      │      │
│  │ Projects        │        │  - Actions       │      │
│  │  - Tasks        │   🎤   │  - Buttons       │      │
│  │  - Dates        │  ASK   │                  │      │
│  └─────────────────┘  ACHIL └──────────────────┘      │
│                        LES                             │
│  ┌─────────────────┐  (sph) ┌──────────────────┐      │
│  │ Notice Board    │        │ User Settings    │      │
│  │  - Updates      │        │  - Name          │      │
│  │  - Activity     │        │  - Company       │      │
│  │                 │        │  - Clearance     │      │
│  └─────────────────┘        └──────────────────┘      │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**Page Header:**
- "User Name  ;  Position" (green, top-left)
- Large text (24-28px)

**Central Achilles Sphere:**
- Position: Dead center of screen
- Size: Large, ~180-220px diameter
- Color: Magenta/pink gradient (#ff1493 → #ff00cc)
- Rim: White/silver striped border
- Icon: White microphone in center
- Text: "Ask Achilles" below (light gray/cyan)
- Glow: Magenta radial glow
- Animation: Pulsing

**Quadrant Layout:**
- 4 panels arranged around central sphere
- Each quadrant: ~40% screen width/height
- Gap: ~40-60px from sphere to each panel edge
- All panels: Glass morphism, cyan border, rounded corners

**Top-Left: "Current Projects"**
- Title: "Current Projects" (white, underlined)
- Content structure:
  - "Project A" (green)
  - "- Task 1 Title  ;  __/__/20__" (green with cyan icons)
  - "- Task 2 Title  ;  __/__/20__" (green with cyan icons)
  - "Project C" (green)
  - "✓ - Task 1 Title  ;  __/__/20__" (green with checkmark)
- Icons: Edit, folder, download icons (cyan) after each task
- Dates in placeholder format

**Top-Right: "Quick Links"**
- Title: "Quick Links" (white, underlined)
- Icons + text layout:
  - ➕ "New Project" (green circle icon + green text)
  - 📋 "New Notice" (green)
  - ✓+ "New Task" (green)
  - ✏️ "Edit Project" (green)
  - ⬆️ "Upload to Archives" (green)
- Top-right corner has calendar and document icons (green)
- Each action is a clickable link

**Bottom-Left: "Notice Board"**
- Title: "Notice Board" (white, underlined)
- Content: Activity feed
  - "✓ Updated X on Y ; __:__ __/__/20__ ; [ User ]" (green checkbox + text)
  - "✓ Uploaded B to Z ; __:__ __/__/20__ ; [ User ]" (green)
  - "✓ Completed X on Y ; __:__ __/__/20__ ; [ User ]" (green)
  - "✓ Open Task for Project C ; TBD __/__/20__ [ User ]" (green)
- All entries: Green with checkboxes
- Time/date stamps
- User tags in brackets

**Bottom-Right: "User Settings"**
- Title: "User Settings" (white, underlined)
- Form fields:
  - "Name : [ _______ ]" (green label, cyan input box)
  - "Company : [ Romer / EMASSC ]" (green label, cyan options)
  - "Position : [ ________ ]" (green label, cyan input)
  - "Clearance : [ Locked Unless Tier 1 ]" (green label, cyan text)
  - "Icon / Photo : [ Dropdown Menu ]" (green label, cyan dropdown)
- All labels in green
- Input fields in cyan boxes
- Consistent spacing

**Scrollbars:**
- Green dots on left/right sides
- Indicate scrollable content
- Vertical position indicators

**Top-Right Corner Icons:**
- Menu icon (hamburger)
- Settings gear
- Consistent positioning

**Purpose:**
- Central dashboard for user
- Quick access to projects, notices, links, settings
- Achilles AI at center of user's world
- **THIS IS THE MAIN DASHBOARD LAYOUT**

---

### Page 12: Radial Menu (Simplified)

**Layout:**
```
┌────────────────────────────────────────────────────────┐
│                    User Name                           │
│                                                        │
│                                                        │
│                   [Projects]                          │
│                       ↑                               │
│          [Notices] ← 🎤 → [Quick]                     │
│                       ↓                               │
│                    [User]                             │
│                                                        │
│                  Ask Achilles                         │
└────────────────────────────────────────────────────────┘
```

**Central Achilles Sphere:**
- Same as Page 11
- Magenta/pink gradient
- White striped rim
- Microphone icon
- Pulsing glow
- Position: Dead center

**Radial Button Layout:**
- 4 buttons in cross pattern (cardinal directions)
- Position: Surrounding sphere at fixed distance (~120-150px from center)
- Shape: Rounded pill buttons
- Color: Green (#00ff88 to #00ff00 gradient)
- Size: ~120-150px wide, 50-60px tall
- Text: White, bold, centered
- Icons: White, on left side of text

**Button Positions:**
- **Top**: "Projects" (building/folder icon)
- **Left**: "Notices" (notice/info icon)
- **Right**: "Quick" (link/chain icon)
- **Bottom**: "User" (person icon)

**Visual Style:**
- Each button has downward-pointing triangle/arrow below text
- Green gradient fill
- Slight glow effect
- Hover state: Brighter glow

**Top Elements:**
- "User Name" centered at top (white, large)

**Bottom Element:**
- "Ask Achilles" centered below sphere (cyan)

**Top-Right Icons:**
- Enter/return icon
- Profile icon (globe with dots)
- Menu icon (hamburger)
- Consistent style

**Background:**
- Same deep blue gradient as all pages
- Radial glow emanating from center sphere

**Purpose:**
- Simplified navigation
- Quick access to 4 main sections
- Radial/circular UI paradigm
- **THIS IS THE SIMPLIFIED MAIN MENU**

---

### Page 13: Flowchart Tree Visualization

**Layout:**
```
┌────────────────────────────────────────────────────────┐
│                                                        │
│                [Central Sphere]                        │
│                                                        │
│   [Node Tree - Hierarchical Layout]                   │
│   Colored rounded rectangles connected by lines       │
│   File stack icons attached to terminal nodes         │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**Central Sphere:**
- Large magenta/pink gradient sphere (center-right area)
- Glowing effect
- Acts as focal point
- May represent root or AI

**Flowchart Nodes:**
- **Shape**: Rounded rectangles (pill-shaped)
- **Colors**:
  - Red (#ff0000, #ff6666)
  - Orange (#ff9900, #ffaa00)
  - Cyan (#00ffff, #00ccff)
  - Green (#00ff00, #66ff66)
  - Magenta (#ff00ff, #ff66ff)
- **Size**: Variable (larger parent nodes, smaller child nodes)
- **Content**: Small white circle on left side of each node
- **Border**: Slight lighter border of same color family

**Connection Lines:**
- **Style**: White or light gray lines
- **Pattern**: Curved/angled connections between nodes
- **Layout**: Hierarchical tree structure
- **Flow**: Left to right expansion

**Hierarchy Structure:**
- Root node (left): Gray rounded square
- Branches out to multiple colored nodes
- Sub-branches: Further expansion
- Multiple levels visible (3-4 levels deep)

**File Stack Icons:**
- **Position**: Terminal nodes (rightmost nodes)
- **Appearance**: Small stack of pages (3-4 layers)
- **Color**: Tan/beige file color
- **Size**: Small, ~20-30px
- **Purpose**: Indicate attached documents/files

**Node Network:**
- Top branch: Red nodes → Orange → Cyan → Files
- Middle branches: Cyan, green, magenta nodes
- Bottom branch: Red → Cyan → Green → Purple → Files
- Complex interconnected structure

**Background:**
- Deep blue gradient (consistent)
- Nodes stand out against dark background

**Top-Right Icons:**
- Settings gear
- Menu icon
- Consistent set

**Purpose:**
- Visualize project/task hierarchies
- Show relationships between components
- Document attachment visualization
- **THIS IS THE FLOWCHART/TREE STRUCTURE VIEW**

---

## COMPONENT LIBRARY CATALOG

### Reusable Components to Build

**1. Achilles Assist Sidebar**
- Glass morphism panel (left fixed)
- Sections: Welcome, Instructions, Input prompt
- Scrollbar with green slider
- Bottom input field with "Add Files" button
- Width: 25% screen
- Height: Full screen

**2. Action Card**
- Large rounded rectangle
- Gradient background (gray to blue-gray)
- Glowing "+" icon (magenta or matching glow)
- Title text (white, Garamond, centered)
- Hover effect: Brightness increase
- Click action: Modal or navigation

**3. Glass Morphism Panel**
- Semi-transparent background
- Cyan 2-3px border
- Rounded corners (15-20px)
- Backdrop blur (10-15px if supported)
- Shadow depth

**4. Breadcrumb Navigation**
- Format: ">Item > Item > ..."
- Green text (#00ff88)
- Monospace font (Consolas)
- Slight glow effect
- Interactive: Click to navigate up hierarchy

**5. Achilles Sphere (3 variants)**
- **Magenta/Pink**: Default AI assistant
- **EMASSC Orange**: Company-specific
- **Römer Teal/Gold**: Company-specific
- Features: Pulsing animation, glow, microphone icon
- Size: Variable (180-250px diameter)

**6. Collapsible Menu**
- Header with underline
- Options list (clickable)
- Sub-options (indented with "Blurb")
- Selected state highlighting
- Expand/collapse animation

**7. Document Page (Single)**
- White background content area
- Cyan border panel
- Scroll bar (green)
- Tool icons (right side)
- Title bar
- Notes section

**8. Stacked Pages Effect**
- 3 layers offset
- Shadow between layers
- Front layer interactive
- Creates depth

**9. Dual-Page Viewer**
- 2 pages side-by-side
- Synchronized scrolling option
- Page navigation
- Metadata sidebar

**10. Radial Button**
- Pill-shaped button
- Green gradient fill
- White text + icon
- Downward arrow indicator
- Glow effect
- Position around central point

**11. Dashboard Quadrant Panel**
- Glass morphism
- Cyan border
- Title with underline
- Content area (scrollable)
- Icons and action buttons
- Variable content types

**12. Flowchart Node**
- Rounded rectangle
- Colored (red, orange, cyan, green, magenta, purple)
- White circle on left
- Connection points
- Clickable/selectable

**13. File Stack Icon**
- 3-4 layered pages
- Offset stacking
- Tan/beige color
- Small size
- Attachment indicator

**14. 3D Grid Visualization Panel**
- Cyan perspective grid
- 3D rendering space
- Curved spacetime effects
- Black hole objects
- Real-time animation

**15. Info Panel (Bottom)**
- Full-width glass morphism
- Title section
- Multi-column text layout
- Real-time data display
- Green/cyan text

**16. Top-Right Icon Set**
- Enter/return icon
- Profile/globe icon
- Settings gear icon
- Menu hamburger icon
- All white with subtle glow
- Fixed position

---

## LAYOUT PATTERNS

### Pattern 1: Sidebar + Cards (Pages 1-4)
```
[Sidebar]  [Card] [Card]
[Input]
```

### Pattern 2: Document Viewer (Pages 5, 10)
```
>Breadcrumb
[Doc Display]  [Side Panel]
[Bottom Info]
```

### Pattern 3: Menu + Sphere (Pages 7-8)
```
[Menu]    [Sphere]    [Menu]
          [Icons]
[Company] [Ask Achilles]
```

### Pattern 4: Visualization (Page 9)
```
>Breadcrumb
[3D Viz Panel]  [Menu]
[Info Panel Full Width]
```

### Pattern 5: Dashboard Quadrants (Page 11)
```
[Projects]      [Quick Links]
        [SPHERE]
[Notice]        [Settings]
```

### Pattern 6: Radial Menu (Page 12)
```
      [Top Button]
[Left] [SPHERE] [Right]
      [Bottom]
```

### Pattern 7: Flowchart (Page 13)
```
[Tree Structure]  [Sphere]
  [Nodes + Files]
```

---

## INTERACTION PATTERNS

### Navigation Hierarchy
1. **Breadcrumbs**: Show current location (">Business > Project > File")
2. **Back Navigation**: Company logo toggles (bottom-left on Pages 7-8)
3. **Ask Achilles**: Always accessible (mic icon)
4. **Top-Right Icons**: Global actions (enter, profile, settings, menu)

### State Indicators
- **Selected**: Cyan highlight or "(Selected)" text
- **Completed**: Green checkmark (✓)
- **Active**: Brighter glow
- **Hover**: Brightness increase, glow intensity

### Animations
- **Sphere Pulse**: 2-3s loop, opacity 0.8 → 1.0
- **Glow Pulse**: Radial glow expands/contracts
- **Menu Expand**: Smooth height animation
- **Card Hover**: Scale 1.0 → 1.02, brightness +10%
- **Loading**: Rotating elements or pulsing

### Input Methods
- **Text Input**: Green labels, cyan input boxes
- **Voice Input**: "Ask Achilles" microphone
- **File Upload**: "Add Files" button (white "+")
- **Clicking**: Cards, buttons, menu items
- **Scrolling**: Custom green scrollbars

---

## SCROLL SYSTEM

### Scrollbar Style
- **Track**: Thin line (white or transparent)
- **Thumb**: Green circular dot or pill
- **Width**: 3-5px for track, 8-12px for thumb
- **Position**: Always visible (no auto-hide)
- **Color**: Green (#00ff88) with slight glow

### Scroll Areas
- Achilles Assist sidebar (vertical)
- Document viewers (vertical)
- Menu panels with many options (vertical)
- Dashboard quadrants with long lists (vertical)
- Flowchart canvas (horizontal + vertical pan)

### Custom Scroll Behavior
- Smooth scrolling (easing function)
- Scroll indicators (dots on sides) for multi-section pages
- Snap-to-section for certain views

---

## RESPONSIVE CONSIDERATIONS

### Window Sizes
- **Minimum**: 1280x720 (HD)
- **Optimal**: 1920x1080 (Full HD)
- **Large**: 2560x1440 (QHD) or ultra-wide

### Scaling Rules
1. **Sphere**: Always centered, scales 0.8x - 1.2x based on viewport
2. **Panels**: Maintain aspect ratio, minimum padding 20px
3. **Text**: Minimum 12px, scales up to 20px for large displays
4. **Icons**: Fixed sizes (40px, 60px, 80px) with SVG for clarity
5. **Cards**: Responsive grid (2-column → 1-column on smaller screens)

---

## ACCESSIBILITY FEATURES

### Color Contrast
- All text on dark blue: Minimum 7:1 contrast ratio
- Green text (#00ff88): High contrast against blue
- White text: Maximum contrast
- Cyan accents: Distinct from background

### Interactive Elements
- Minimum touch target: 44x44px
- Clear focus indicators (brighter glow)
- Keyboard navigation support
- Screen reader labels for icons

### Visual Indicators
- Not solely color-dependent (use icons + text)
- Motion can be disabled (reduce pulse animations)
- High contrast mode available

---

## IMPLEMENTATION PRIORITY

### Phase 1: Core Components (Week 1)
1. Color system constants
2. Typography system (Garamond + fonts)
3. Glass morphism panel component
4. Achilles sphere (all variants)
5. Action card component

### Phase 2: Layout Systems (Week 2)
6. Sidebar + cards layout
7. Dashboard quadrants layout
8. Radial menu layout
9. Breadcrumb navigation
10. Top-right icon set

### Phase 3: Complex Components (Week 3)
11. Collapsible menu
12. Document viewer (single + dual)
13. Stacked pages effect
14. Flowchart system
15. 3D visualization panel

### Phase 4: Interactions (Week 4)
16. Animations (pulse, glow, hover)
17. Custom scrollbars
18. State management (selected, active)
19. Voice input integration
20. File upload system

---

## TECHNICAL REQUIREMENTS

### GUI Framework Decision

**Option 1: PyQt6/PySide6**
- ✅ Can do glass morphism (QGraphicsBlurEffect)
- ✅ Rounded corners (QPainterPath)
- ✅ Gradients and glow effects (QPainter)
- ✅ Custom scrollbars (QScrollBar styling)
- ✅ Animations (QPropertyAnimation)
- ❌ 3D integration more complex

**Option 2: Web-Based (Electron + HTML/CSS/JS + Three.js)**
- ✅ Glass morphism (CSS backdrop-filter)
- ✅ Rounded corners (border-radius)
- ✅ Gradients (CSS gradients)
- ✅ Glow effects (box-shadow, filter)
- ✅ Animations (CSS transitions, keyframes)
- ✅ 3D integration (Three.js native)
- ✅ Flowcharts (D3.js, vis.js)
- ✅ Custom scrollbars (CSS)
- ❌ More complex deployment

**Option 3: CustomTkinter**
- ✅ Modern look
- ❌ Limited glass morphism
- ❌ No native blur effects
- ❌ Harder to achieve exact aesthetic

**RECOMMENDATION: Web-based (Electron + React/Vue + Three.js)**
- Best match for UI Base.pdf aesthetic
- Modern effects built-in
- 3D integration straightforward
- Rich ecosystem for components

---

## CONCLUSION

This specification provides **complete, pixel-perfect requirements** for implementing the UI Base.pdf aesthetic across all 13 pages. Every color code, font choice, layout pattern, and interaction has been documented.

**Key Takeaways:**
1. **Deep blue gradient background** (#000033 → #0000ff) is MANDATORY
2. **Cyan/magenta/green accent system** is the core color palette
3. **Glass morphism** is the dominant panel style
4. **Garamond typography** for all headers/titles
5. **Achilles sphere** is the central UI element (always visible)
6. **Breadcrumb navigation** shows hierarchy (green monospace)
7. **Radial layouts** are preferred over linear
8. **7 distinct layout patterns** for different functions
9. **Pulsing/glowing animations** bring UI to life
10. **Web-based framework** recommended for implementation

**Next Steps:**
1. Choose framework (recommend Electron + React + Three.js)
2. Build component library matching this spec
3. Implement each page layout
4. Test aesthetic fidelity against UI Base.pdf
5. Integrate with existing LightSpeed backend

---

*Specification Complete: January 5, 2026*
*Source: UI Base.pdf (13 pages)*
*Total Components Catalogued: 16*
*Total Layout Patterns: 7*
*Total Pages Specified: 13*
