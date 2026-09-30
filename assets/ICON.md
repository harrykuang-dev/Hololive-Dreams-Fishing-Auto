# Fish application icon

## 1.0 Windows readability revision (current)

The active EXE, main window and help dialog use `fish-clear.ico`. Its artwork is
`fish-clear.png`, edited with the built-in imagegen tool (not the API/CLI).
The target is recognizability at **32x32**, retaining the pirate hat, eye, purple
lips and fins. The hat emblem is an arrow piercing a heart split into white and
dark halves, as confirmed by the user; it is neither a skull nor a planet.
Fine body-heart/anchor decorations were removed. The rejected minimal
variant is retained as `fish-simple.png`; previous assets are also preserved.

Base generation prompt (the skull request was a mistake, corrected below):

> Create a balanced medium-detail pixel-art Windows application icon using these two references: the first shows the original red/orange pirate fish identity, the second shows the overly simplified version. The user rejects BOTH excessive original detail and the overly basic fish shape. TARGET is a clear, attractive 32x32 icon, NOT a 16x16 minimal logo. Restore the original fish character's personality: a round red-orange body facing left, dark purple pirate tricorne with a broad golden rim and a small simple white skull mark, a large expressive white/gold eye with dark pupil and ONE white glint, short plump purple lips, ONE small purple pectoral fin, broad purple lower fin, and fan-shaped red tail with TWO broad lighter rays. Allow 2 or 3 large orange scale-shaped patches on the body, but remove anchor, hearts, elaborate ornament, feather, tiny lines and fine textures. Cute confident pirate mascot. Use an intentional genuine 32x32 pixel grid, each design pixel enlarged uniformly: crisp chunky stepped silhouette with single-pixel conceptual dark-purple outline, compact approximately square composition occupying about 90% canvas. About 10-12 well-separated solid colors, no smooth gradients, dithering or painting texture. Hat should remain clearly recognizable and not dominate the whole fish. Eye about 5x5 conceptual pixels, lips about 3x3, broad fin about 5x3. Real transparent background, entire fish unclipped, no text, watermark, shadow, border, other objects or multi-icon sheet. Medium detail: retain pirate fish features, but every feature must remain legible at 32x32.

Earlier emblem interpretation (incorrect; superseded by the prompt below):

> Localized correction only. The first reference is the current pixel pirate fish Windows application icon. Preserve this exact icon's medium-detail 32x32-friendly style, silhouette, hat outline, gold brim, red-orange fish, eye, purple lips, fins and tail. Change ONLY the white emblem on the left/front of the hat. It is NOT a skull, NOT crossbones, and NOT a pirate Jolly Roger. Replace the skull with the actual white hat emblem visible in the second reference photo. The emblem is a stylized ringed planet / orbital symbol: a tilted rounded planetary loop, lower-left white crescent/solid rounded area, a diagonal narrow tilted orbital ring crossing it from upper left toward lower right, with a short upward-left stem and tiny crossing stroke. Match the photo's silhouette and simplify this specific emblem into a bold white pixel cluster recognizable at 32x32. It must have no face, no eye sockets, no teeth. Do not import any objects from the mannequin or jewelry in photo, do not change the rest of the fish or hat. Do not add text, border or watermark. Keep a truly transparent background. Chunky crisp pixel-art color clusters, no smooth gradients, no dithering, no added shading.

Final correction prompt:

> Change ONLY the white emblem on the pirate hat in the first image. Preserve the exact red-orange fish, purple lips and fins, expressive eye, gold-trimmed purple hat, tail, medium-detail pixel-art style, composition and transparent background. The second image is the actual emblem reference; the user explicitly confirms its meaning: AN ARROW PIERCING A HEART, with the heart split into BLACK AND WHITE HALVES. It is NOT a skull, NOT a ringed planet, NOT an orbit. Render a recognizable heart with two upper lobes, a cleft, and a pointed bottom, tilted as in the reference photograph. One half is solid white (left/lower side), the other half black/dark purple (right/upper side) enclosed by a bold white outline. A single straight arrow runs diagonally from upper left through the heart toward lower right, with a small tail/feather at the upper-left end and a triangular arrowhead at the lower-right end. Match the reference white-versus-dark split-heart shape closely. Use crisp simple white pixel clusters on the purple hat; make it about 5-6 conceptual pixels wide for clarity in a 32x32 Windows icon. No eyes, mouth, tooth shapes, circular planetary ring, or extra heart elsewhere. LOCAL edit only, do not redesign the fish or the rest of the hat. No text, watermark, border or background. Truly transparent PNG.

Package with `python tools/make_icon.py assets/fish-clear.png assets/fish-clear.ico --pixel`.
The script only crops transparent padding, resizes and packages the artwork;
it does not paint or change the design. Nearest-neighbor resizing was selected
after inspecting the actual 32-pixel frames against smooth resizing.
The ICO contains explicit 16/20/24/28/32/40/48/56/60/64/72/80/96/128/256-pixel
frames, including intermediate Windows DPI sizes. Both the EXE resource and Tk
windows must use this icon. A new taskbar AppUserModelID distinguishes this icon
revision from the older one; old pinned shortcuts may still need to be repinned.

Visual QA: `python tools/preview_icon.py` writes `build/icon-comparison.png`,
comparing old/new native frames and enlarged pixels on light/dark backgrounds.
The preview is not an artwork source. Run `python -m unittest discover -s tests -v`
to validate transparency, size coverage and exact packaging reproducibility.

## 1.0 pixel-art icon

`fish-pixel.png` is the previous static pixel-style variant made with the built-in imagegen tool using `fish-cutout.png` as the edit target. It is not an animated pet or an installed ChatGPT asset. Its seven-size ICO remains as a comparison asset; it is no longer the EXE/window icon.

Final prompt:

> Use case: style-transfer. Edit target: the reference red/orange pirate fish illustration. Asset type: single static Windows application icon, NOT an animated pet or sprite sheet. Transform this exact character into a cute chunky pixel-art desktop-pet-style icon optimized to remain recognizable at 16x16 and 32x32. Keep the left-facing round red/orange fish, oversized dark purple pirate tricorne with gold trim, one expressive large eye, purple lips/fins, and fan tail. Simplify tiny scales, ornaments and texture into strong flat color clusters. Prioritize a broad hat silhouette, bright red fish body, large eye and clearly separated tail. Compact almost-square composition, fill the square canvas with the whole character leaving only a 1-2-pixel conceptual margin. Design like a deliberately hand-pixeled 32x32 sprite enlarged with nearest-neighbor: very coarse uniform square pixel grid, crisp hard edges, thick dark-purple stepped outline, limited palette about 12 colors, no antialiasing, no gradients, no micro-details or excessive empty space. Genuinely transparent background and clean alpha. No text, watermark, border, scenery or additional objects.

Package the icon using `python tools/make_icon.py assets/fish-pixel.png assets/fish-pixel.ico --pixel`. Each ICO size is explicitly resized using nearest-neighbor and supplied as a pre-sized frame, avoiding smooth interpolation inside the ICO writer. Only file-format conversion, transparent margin and size preparation are performed by this script; style transfer is performed by imagegen.

## Original 0.4.0 cutout

`fish-cutout.png` is the transparent cutout of the fish supplied by the user.
It was edited using the built-in imagegen tool (not the API/CLI). It is used only
for the fishing assistant EXE/window icon; no game files are modified.

Final prompt:

> Use case: background-extraction. Edit target: the supplied fish illustration. Remove ONLY the cream background and faint circular Fishing watermark behind the fish. Preserve the exact red/orange fish, pirate hat, fins, face, proportions, linework, colors, and all details unchanged. Clean edge cutout, genuinely transparent alpha background, entire fish visible with modest transparent padding. No new objects, text, shadows or redesign. Intended for Windows application icon.

`tools/make_icon.py` converts the transparent PNG to `fish.ico`, with transparent
square padding and 16/24/32/48/64/128/256-pixel sizes. It does not remove or repaint
the background. Rebuild with `python tools/make_icon.py assets/fish-cutout.png assets/fish.ico`.
