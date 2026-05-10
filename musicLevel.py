import math
import random

import pygame
import pytmx
import pyscroll

from player import PlayerShadow
from inventory import Inventory



class _CollectedInstrument:
    """Lightweight inventory entry for a grabbed instrument."""
    def __init__(self, name, image):
        self.name          = name
        self.display_image = image   # used by Inventory.draw via hasattr check


class MusicLevel:
    # Names that can appear as named "obj" collision walls in the TMX
    _INSTRUMENT_NAMES = {"Guitar", "Maracas", "Trumpet", "Violin", "Harp", "Cymbals"}

    # Sound file for each map instrument — all are now .mp3
    _INSTRUMENT_SOUNDS = {
        "Guitar":  "music/instSound/levelInstruments/Guitar.mp3",
        "Maracas": "music/instSound/levelInstruments/Maracas.mp3",
        "Trumpet": "music/instSound/levelInstruments/Trumpet.mp3",
        "Violin":  "music/instSound/levelInstruments/Violin.mp3",
        "Harp":    "music/instSound/levelInstruments/Harp.mp3",
        "Cymbals": "music/instSound/levelInstruments/Cymbals.mp3",
    }

    def __init__(self, screen, game_instance):
        self.screen = screen
        self.game   = game_instance

        self.game.music.stop()

        # ── Map ───────────────────────────────────────────────────────────
        self.tmx_data = pytmx.util_pygame.load_pygame("musicLevel.tmx")

        # Layer order is set in Tiled. onTop and everything above it in the TMX
        # renders above the player; everything below onTop renders beneath him.
        # Find the TMX index of 'onTop' and place the player sprite just before it.
        _all_layers = list(self.tmx_data.layers)
        _ontop_idx  = next((i for i, l in enumerate(_all_layers)
                            if getattr(l, 'name', '') == 'onTop'), len(_all_layers))
        _player_layer = max(_ontop_idx - 1, 0)

        map_data       = pyscroll.data.TiledMapData(self.tmx_data)
        self.map_layer = pyscroll.orthographic.BufferedRenderer(
            map_data, self.screen.get_size()
        )
        self.map_layer.zoom    = 3
        self.map_layer.bgcolor = (36, 34, 39)

        # ── Player ────────────────────────────────────────────────────────
        self.player = game_instance.player

        self.group = pyscroll.PyscrollGroup(map_layer=self.map_layer,
                                            default_layer=_player_layer)

        self.player_shadow = PlayerShadow(self.player)
        self.group.add(self.player_shadow)
        self.group.change_layer(self.player_shadow, max(_player_layer - 1, 0))

        self.group.add(self.player)
        self.group.change_layer(self.player, _player_layer)

        # zoom factor — needed for the glow pre-scale below
        _zoom = int(self.map_layer.zoom)

        # Reference tick for frame-rate-independent movement
        self._last_tick = pygame.time.get_ticks()

        # ── E badges (yellow / amber theme) ──────────────────────────────
        _BG     = ( 20,  15,   0, 200)
        _TEAL   = (255, 210,   0, 255)   # bright yellow (border / note icon)
        _PURPLE = (200, 130,   0, 255)   # amber (inner border / key outline)
        _KEY_BG = ( 35,  25,   0, 250)
        _TEXT   = (255, 245, 170, 255)   # warm light yellow

        _font     = pygame.font.Font("fonts/Pixel Emulator.otf", 18)
        _key_surf = _font.render("E", True, _TEXT)

        _NOTE_BITMAP = [
            "...###",
            "....##",
            ".....#",
            ".....#",
            ".....#",
            ".....#",
            "..####",
            "..####",
            ".....#",
            ".####.",
            ".####.",
        ]
        _CELL   = 2
        _note_w = len(_NOTE_BITMAP[0]) * _CELL
        _note_h = len(_NOTE_BITMAP)    * _CELL
        _pad    = 7
        _key_sz = _key_surf.get_height() + _pad * 2

        def _make_badge(hint_text: str) -> pygame.Surface:
            hs = _font.render(hint_text, True, _TEXT)
            bw = _pad + _note_w + _pad + _key_sz + hs.get_width() + _pad * 2
            bh = _key_sz + _pad * 2
            s  = pygame.Surface((bw, bh), pygame.SRCALPHA)
            pygame.draw.rect(s, _BG,     (0, 0, bw, bh))
            pygame.draw.rect(s, _TEAL,   (0, 0, bw, bh), 2)
            pygame.draw.rect(s, _PURPLE, (3, 3, bw - 6, bh - 6), 1)
            nx, ny = _pad, (bh - _note_h) // 2
            for ri, row in enumerate(_NOTE_BITMAP):
                for ci, px in enumerate(row):
                    if px == "#":
                        pygame.draw.rect(s, _TEAL,
                                         (nx + ci * _CELL, ny + ri * _CELL, _CELL, _CELL))
            kx, ky = _pad + _note_w + _pad, _pad
            pygame.draw.rect(s, _KEY_BG, (kx, ky, _key_sz, _key_sz))
            pygame.draw.rect(s, _PURPLE, (kx, ky, _key_sz, _key_sz), 2)
            pygame.draw.rect(s, _TEAL,   (kx + 2, ky + 2, 3, 1))
            s.blit(_key_surf, (kx + (_key_sz - _key_surf.get_width())  // 2,
                               ky + (_key_sz - _key_surf.get_height()) // 2))
            s.blit(hs,        (kx + _key_sz + _pad,
                               ky + (_key_sz - hs.get_height()) // 2))
            return s

        self.e_badge    = _make_badge("interact")
        self.play_badge = _make_badge("play")
        # ─────────────────────────────────────────────────────────────────

        # ── Object loading ────────────────────────────────────────────────
        self.walls: list[pygame.Rect] = []

        # name → [pygame.Rect, ...] — walls that belong to a specific instrument;
        # removed when that instrument is collected.
        self.instrument_walls: dict[str, list[pygame.Rect]] = {}

        # type="instruments" zones: [{name, rect}, ...]
        self.instrument_zones: list[dict] = []

        # All podium rects (type-agnostic, matched by name)
        self.podiums: list[pygame.Rect] = []

        spawn_points: list[tuple] = []

        for obj in self.tmx_data.objects:

            if obj.type == "obj":
                r = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                if obj.name and obj.name in self._INSTRUMENT_NAMES:
                    self.instrument_walls.setdefault(obj.name, []).append(r)
                else:
                    self.walls.append(r)

            elif obj.type == "instruments":
                self.instrument_zones.append({
                    "name": obj.name,
                    "rect": pygame.Rect(obj.x, obj.y, obj.width, obj.height),
                })

            if obj.name and obj.name.lower() == "podium":
                self.podiums.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

            if obj.name and obj.name.lower() == "player":
                spawn_points.append((obj.x, obj.y))

        if spawn_points:
            spawn = random.choice(spawn_points)
            self.player.position[0] = spawn[0]
            self.player.position[1] = spawn[1]
            self.player.rect.topleft = self.player.position

        # ── Glow layer ────────────────────────────────────────────────────
        # Tiles are pre-scaled once at zoom resolution and blitted directly to
        # the screen via translate_point — no pyscroll sprite, no sprite_damage.
        # Glow timing: 333 ms fade-in → 333 ms fade-out (≈ 20 frames at 60 fps).
        self._GLOW_HALF_MS  = 600
        self._glow_start_ms = 0   # get_ticks() value when the current cycle began
        # Each entry is a sprite added to the pyscroll group at the layer below
        # the player so pyscroll's z-ordering keeps it under the player and
        # under the onTop layer.  All sprites share the same alpha/timing.
        self._glow_sprites: list[pygame.sprite.Sprite] = []

        _tw = self.tmx_data.tilewidth
        _th = self.tmx_data.tileheight

        def _load_glow_layer(name: str):
            try:
                _gl = self.tmx_data.get_layer_by_name(name)
                _gl.visible = False
                self.map_layer.set_size(self.screen.get_size())
                _tiles = [(gx, gy, gid) for gx, gy, gid in _gl if gid != 0]
                if not _tiles:
                    return
                _min_gx = min(t[0] for t in _tiles)
                _min_gy = min(t[1] for t in _tiles)
                _max_gx = max(t[0] for t in _tiles) + 1
                _max_gy = max(t[1] for t in _tiles) + 1
                _iw = (_max_gx - _min_gx) * _tw
                _ih = (_max_gy - _min_gy) * _th
                # Pre-render once into a plain surface + colorkey so that
                # set_alpha() can be used for fading — zero per-frame work.
                _img_surf = pygame.Surface((_iw, _ih))
                _img_surf.fill((0, 0, 0))
                _base = pygame.Surface((_iw, _ih), pygame.SRCALPHA)
                for _gx, _gy, _gid in _tiles:
                    _img = self.tmx_data.get_tile_image_by_gid(_gid)
                    if _img:
                        _base.blit(_img, ((_gx - _min_gx) * _tw,
                                          (_gy - _min_gy) * _th))
                _img_surf.blit(_base, (0, 0))
                _img_surf.set_colorkey((0, 0, 0))
                _img_surf.set_alpha(0)          # starts invisible
                _gs        = pygame.sprite.Sprite()
                _gs.image  = _img_surf
                _gs.rect   = pygame.Rect(_min_gx * _tw, _min_gy * _th, _iw, _ih)
                self.group.add(_gs)
                self.group.change_layer(_gs, max(_player_layer - 2, 0))
                self._glow_sprites.append(_gs)
            except (ValueError, AttributeError):
                pass

        _load_glow_layer("glow1")
        _load_glow_layer("glow2")

        # ── State ─────────────────────────────────────────────────────────
        self.collected: set[str] = set()

        # Name of the instrument currently being challenged (None = no challenge)
        self.active_challenge: str | None = None

        # Inventory
        self.inventory = Inventory()

        # ── Visual effects ────────────────────────────────────────────────
        self._wrong_flash      = 0
        self._wrong_flash_surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)

        # ── Attempts ──────────────────────────────────────────────────────
        self.attempts = 3

        # ── Cached HUD surfaces ───────────────────────────────────────────
        # Font is loaded once; text surfaces are re-rendered only when the
        # displayed values change (collected count or active challenge text).
        self._hud_font         = pygame.font.Font("fonts/Pixel Emulator.otf", 26)
        self._hud_surf: pygame.Surface | None = None
        self._hud_cache_key    = None
        self._att_surf: pygame.Surface | None = None   # cached attempts badge (left side)
        self._att_key          = None                  # attempts value when last rendered

        # Wave-bar panel background — fixed size, allocated once.
        _N_BARS, _BAR_W, _GAP, _MAX_H, _PAD, _PPPAD = 14, 8, 3, 55, 12, 6
        _panel_w = _N_BARS * _BAR_W + (_N_BARS - 1) * _GAP + _PPPAD * 2
        _panel_h = _MAX_H + _PPPAD * 2
        self._wave_panel_bg = pygame.Surface((_panel_w, _panel_h), pygame.SRCALPHA)
        self._wave_panel_bg.fill((20, 15, 0, 190))
        pygame.draw.rect(self._wave_panel_bg, (255, 210, 0, 200),
                         (0, 0, _panel_w, _panel_h), 2)
        self._wave_panel_size = (_panel_w, _panel_h)

        self._glow_active  = False
        self._glow_looping = False
        self._glow_alpha   = 0

        # Cached wall list — rebuilt only when an instrument is collected.
        self._walls_dirty  = True
        self._walls_cache: list = []

        # Per-frame cache: set once per update(), read by drawing_e() and E handler.
        self._frame_interactable: str | None = None

        # ── Sounds ───────────────────────────────────────────────────────
        # Preload all instrument sounds as pygame.mixer.Sound objects so they
        # can be played on a dedicated channel (looping) independently of
        # pygame.mixer.music.
        self._sounds: dict[str, pygame.mixer.Sound | None] = {}
        for inst_name, path in self._INSTRUMENT_SOUNDS.items():
            try:
                snd = pygame.mixer.Sound(path)
                snd.set_volume(0.7)
                self._sounds[inst_name] = snd
            except Exception as e:
                print(f"[MusicLevel] Could not load sound '{path}': {e}")
                self._sounds[inst_name] = None

        # Dedicated mixer channel for the looping challenge sound so we can
        # stop it cleanly without affecting other channels.
        self._challenge_channel: pygame.mixer.Channel = pygame.mixer.Channel(7)

        try:
            _raw = pygame.mixer.Sound("music/failSound.wav")
            self._fail_sound = self._trim_silence(_raw)
            self._fail_sound.set_volume(0.8)
        except Exception as e:
            print(f"[MusicLevel] Could not load fail sound: {e}")
            self._fail_sound = None

    # ------------------------------------------------------------------ #
    @staticmethod
    def _trim_silence(sound: pygame.mixer.Sound,
                      threshold: int = 200) -> pygame.mixer.Sound:
        """Return a new Sound with leading silence stripped.

        Scans sample amplitudes and cuts everything before the first frame
        that exceeds `threshold` (0-32767 scale for 16-bit audio).
        Falls back to the original Sound if numpy is unavailable or the
        array is already non-silent from the start.
        """
        try:
            import numpy as np
            arr = pygame.sndarray.array(sound)           # shape: (frames,) or (frames, ch)
            amps = np.max(np.abs(arr), axis=-1) if arr.ndim == 2 else np.abs(arr)
            hits = np.where(amps > threshold)[0]
            if len(hits) == 0 or hits[0] == 0:
                return sound
            return pygame.sndarray.make_sound(arr[hits[0]:].copy())
        except Exception:
            return sound

    # ------------------------------------------------------------------ #
    #  Challenge helpers
    # ------------------------------------------------------------------ #
    def _uncollected_zones(self) -> list[dict]:
        return [z for z in self.instrument_zones if z["name"] not in self.collected]

    def _start_challenge(self):
        """Pick a random uncollected instrument, play its sound on loop."""
        candidates = self._uncollected_zones()
        if not candidates:
            return   # all done

        # If a challenge is already running, stop it first
        self._challenge_channel.stop()

        chosen = random.choice(candidates)
        self.active_challenge = chosen["name"]

        snd = self._sounds.get(self.active_challenge)
        if snd:
            self._challenge_channel.play(snd, loops=-1)

        print(f"[MusicLevel] Challenge started: find the {self.active_challenge}")

    def _try_collect(self, zone: dict):
        """Called when the player presses E on an instrument zone.

        • Correct instrument (matches active challenge) → collect it, stop loop.
        • Wrong instrument → nothing happens.
        • No challenge active → nothing happens (must interact with Podium first).
        """
        if self.active_challenge is None:
            return

        name = zone["name"]
        if name != self.active_challenge:
            self.attempts -= 1
            self._wrong_flash = 35
            if self._fail_sound:
                self._fail_sound.play()
            return

        # ── Correct! ──────────────────────────────────────────────────────
        self._challenge_channel.stop()
        self.active_challenge = None
        self._glow_looping    = False
        self._glow_active     = False
        self._glow_alpha      = 0
        self._collect_instrument(zone)

    def _collect_instrument(self, zone: dict):
        """Hide tile layer, remove walls, add to inventory, play pickup sound."""
        name = zone["name"]
        if name in self.collected:
            return
        self.collected.add(name)

        # 1. Hide the matching tile layer
        try:
            layer = self.tmx_data.get_layer_by_name(name)
            layer.visible = False
            self.map_layer.set_size(self.screen.get_size())
        except (ValueError, AttributeError) as e:
            print(f"[MusicLevel] Could not hide layer '{name}': {e}")

        # 2. Remove named collision walls for this instrument
        if name in self.instrument_walls:
            del self.instrument_walls[name]
            self._walls_dirty = True

        # 3. Load image → inventory
        img_path = f"images/instruments/{name}.png"
        try:
            img = pygame.image.load(img_path).convert_alpha()
        except Exception as e:
            print(f"[MusicLevel] Image load failed '{img_path}': {e}")
            img = pygame.Surface((1, 1), pygame.SRCALPHA)

        self.inventory.add_item(_CollectedInstrument(name, img))
        print(f"[MusicLevel] Collected: {name}")

    # ------------------------------------------------------------------ #
    #  Collision
    # ------------------------------------------------------------------ #
    def _all_walls(self) -> list[pygame.Rect]:
        if self._walls_dirty:
            self._walls_cache = list(self.walls)
            for rects in self.instrument_walls.values():
                self._walls_cache.extend(rects)
            self._walls_dirty = False
        return self._walls_cache

    # ------------------------------------------------------------------ #
    #  Input / drawing
    # ------------------------------------------------------------------ #
    def handle_input(self, dt: float):
        keys = pygame.key.get_pressed()
        if not self.player.canMove:
            return

        self.player.walking = False
        dx = dy = 0

        if keys[pygame.K_UP]:
            dy -= 1;  self.player.direction = "up";    self.player.walking = True
        elif keys[pygame.K_DOWN]:
            dy += 1;  self.player.direction = "down";  self.player.walking = True

        if keys[pygame.K_LEFT]:
            dx -= 1;  self.player.direction = "left";  self.player.walking = True
        elif keys[pygame.K_RIGHT]:
            dx += 1;  self.player.direction = "right"; self.player.walking = True

        direction = pygame.math.Vector2(dx, dy)
        if direction.length() > 0:
            direction = direction.normalize()

        self.player.save_location()
        # Multiply by dt*60 so speed stays calibrated at 60 fps regardless of
        # the actual frame rate (dt is in seconds; dt*60 ≈ 1 at 60 fps).
        self.player.position[0] += direction.x * self.player.speed * dt * 60
        self.player.position[1] += direction.y * self.player.speed * dt * 60
        self.player.animate()

    def _near_interactable(self) -> str | None:
        """Return 'podium' or 'instrument' if near something interactable, else None."""
        if any(self.player.feet.colliderect(p) for p in self.podiums):
            if self._uncollected_zones():
                return "podium"
        for zone in self._uncollected_zones():
            if self.player.feet.colliderect(zone["rect"]):
                return "instrument"
        return None

    _WAVE_FREQS  = [1.7, 2.3, 1.1, 3.1, 2.7, 1.5, 3.7, 2.1, 1.3, 2.9, 1.9, 3.3, 2.5, 1.6]
    _WAVE_PHASES = [0.0, 0.8, 1.6, 0.4, 2.1, 1.2, 0.3, 1.9, 0.9, 2.5, 0.6, 1.4, 2.8, 0.2]

    def _draw_wave_bar(self):
        """Attempts badge + equalizer bars stacked on the top-left during a challenge."""
        if not self.active_challenge:
            return

        N_BARS    = 14
        BAR_W     = 8
        GAP       = 3
        MAX_H     = 55
        MIN_H     = 4
        PAD       = 12
        PANEL_PAD = 6

        # ── Attempts badge (cached) ───────────────────────────────────────
        if self.attempts != self._att_key:
            pad  = 8
            text = self._hud_font.render(f"Attempts  {self.attempts}/3", False, (255, 215, 0))
            bg   = pygame.Surface((text.get_width() + pad * 2,
                                   text.get_height() + pad * 2), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 130))
            bg.blit(text, (pad, pad))
            self._att_surf = bg
            self._att_key  = self.attempts
        self.screen.blit(self._att_surf, (PAD, PAD))

        top = PAD + self._att_surf.get_height() + 4

        t = pygame.time.get_ticks() / 1000.0
        self.screen.blit(self._wave_panel_bg, (PAD, top))

        base_y = top + PANEL_PAD + MAX_H
        for i in range(N_BARS):
            raw = (math.sin(t * self._WAVE_FREQS[i] + self._WAVE_PHASES[i]) + 1) / 2
            h   = int(MIN_H + raw * (MAX_H - MIN_H))
            g   = int(210 - (h / MAX_H) * 110)
            x   = PAD + PANEL_PAD + i * (BAR_W + GAP)
            pygame.draw.rect(self.screen, (255, max(g, 0), 0),
                             (x, base_y - h, BAR_W, h))

    def drawing_e(self):
        """Draw the appropriate E badge above the player when near something interactable."""
        if self.inventory.open:
            return
        kind = getattr(self, '_frame_interactable', None)
        if kind is None:
            return

        badge = self.play_badge if kind == "podium" else self.e_badge
        bob   = math.sin(pygame.time.get_ticks() / 200) * 5
        _zoom = int(self.map_layer.zoom)
        px, py = self.map_layer.translate_point(self.player.position)
        bx = px + (self.player.rect.width * _zoom) // 2 - badge.get_width() // 2
        by = py - badge.get_height() - 8 + int(bob)
        self.screen.blit(badge, (bx, by))

    def _draw_wrong_flash(self):
        """Low-opacity red screen splash that fades when the wrong instrument is picked."""
        if self._wrong_flash <= 0:
            return
        t = self._wrong_flash / 35   # 1.0 → 0.0
        self._wrong_flash -= 1

        self._wrong_flash_surf.fill((210, 0, 0, int(t * 110)))
        self.screen.blit(self._wrong_flash_surf, (0, 0))

    def _draw_hud(self):
        """Instruments counter — top right."""
        cache_key = (len(self.collected),)
        if cache_key != self._hud_cache_key:
            total = len(self.instrument_zones)
            pad   = 8
            text  = self._hud_font.render(f"Instruments  {len(self.collected)}/{total}",
                                          False, (255, 215, 0))
            bg = pygame.Surface((text.get_width() + pad * 2,
                                 text.get_height() + pad * 2), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 130))
            bg.blit(text, (pad, pad))
            self._hud_surf      = bg
            self._hud_cache_key = cache_key

        if self._hud_surf:
            x = self.screen.get_width() - self._hud_surf.get_width() - 12
            self.screen.blit(self._hud_surf, (x, 12))

    # ------------------------------------------------------------------ #
    def update(self, events):
        _now = pygame.time.get_ticks()
        dt   = min((_now - self._last_tick) / 1000.0, 0.05)  # cap at 50 ms
        self._last_tick = _now

        self.player.save_location()
        self.handle_input(dt)

        # ── Glow sprite images updated before draw so pyscroll z-orders them
        # below the player and below the onTop layer.
        if self._glow_sprites:
            if self._glow_active or self._glow_looping:
                _now_ms  = pygame.time.get_ticks()
                _elapsed = _now_ms - self._glow_start_ms
                _half    = self._GLOW_HALF_MS
                _full    = _half * 2
                if _elapsed < _full:
                    if _elapsed < _half:
                        alpha = int(_elapsed / _half * 255)
                    else:
                        alpha = int((_full - _elapsed) / _half * 255)
                    self._glow_alpha  = max(0, min(255, alpha))
                    self._glow_active = True
                else:
                    if self._glow_looping:
                        self._glow_start_ms = _now_ms   # restart cycle
                        self._glow_alpha    = 0
                    else:
                        self._glow_alpha  = 0
                        self._glow_active = False

            _a = self._glow_alpha if (self._glow_active and self._glow_alpha > 0) else 0
            for _gs in self._glow_sprites:
                _gs.image.set_alpha(_a)

        self.group.update()
        self.group.center(self.player.rect)
        self.group.draw(self.screen)

        # Cache interactable kind for this frame (used by drawing_e and event handler)
        self._frame_interactable = self._near_interactable()

        self.drawing_e()
        self._draw_hud()
        self._draw_wave_bar()
        self._draw_wrong_flash()

        if self.player.feet.collidelist(self._all_walls()) > -1:
            self.player.move_back()

        if self.inventory.open:
            self.inventory.draw(self.screen)

        for event in events:
            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_i:
                    self.inventory.open_sound.play()
                    self.inventory.open = not self.inventory.open
                    self.player.canMove = not self.inventory.open

                if event.key == pygame.K_e and not self.inventory.open:
                    kind = self._frame_interactable

                    if kind == "podium":
                        self._start_challenge()
                        self._glow_looping   = True
                        self._glow_start_ms  = pygame.time.get_ticks()

                    elif kind == "instrument":
                        # Find which zone the player is in and try to collect
                        for zone in self._uncollected_zones():
                            if self.player.feet.colliderect(zone["rect"]):
                                self._try_collect(zone)
                                break

        # ── Lose condition ───────────────────────────────────────────────
        if self.attempts <= 0:
            self._challenge_channel.stop()
            self.game.display_entering_message(
                ["You've run out of attempts.",
                 "Listen more carefully next time."]
            )
            self.game.map = "world"

        # ── Win condition ────────────────────────────────────────────────
        all_names = {z["name"] for z in self.instrument_zones}
        if self.collected >= all_names and all_names:
            self._challenge_channel.stop()
            self.game.display_entering_message(
                ["Congratulations! You collected all the instruments.",
                 "You have the ear of a true musician."]
            )
            self.game.music.load("music/pottery level music.aif")
            self.game.music.play(-1)
            self.game.music.set_volume(0.5)
            self.game.map = "world"
            self.game.music_level_completed = True
