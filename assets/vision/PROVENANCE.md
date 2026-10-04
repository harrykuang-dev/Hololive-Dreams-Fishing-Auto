# TAP shape reference

`tap_letters.png` is a 144 × 46 grayscale letter mask (1,606 bytes), derived
from `ui_230_txt_tap` in the installed Windows game's `ParkFishingAtlas`.
The colored sprite and full atlas are not bundled in this assistant.
The artwork belongs to the game's rights holders, as described in the README.

Extraction was validated on 2026-10-04 using
[CyleAR/hololive-toolkit](https://github.com/CyleAR/hololive-toolkit)
commit `8089309806b10ce6cc0ae660a46d2217eb815a1e`,
`extractor.extract_asset_bundle(..., textures_only=True)`.
Local Addressables bundle: `8121ee6103b68e75fb1a016b3e477640.bundle`.

Rebuild with `python tools/prepare_ui_templates.py PATH/TO/ui_230_txt_tap.png`.
The assistant reads its bundled mask; users need neither toolkit nor access
to installed game files. A mask match must also pass independent blue-outline
and exclamation checks before a TAP decision is returned.
