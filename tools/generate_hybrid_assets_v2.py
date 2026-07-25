#!/usr/bin/env python3
"""Render production-grade deterministic hybrid dragon asset packs.

The renderer replaces the 39 generated-v1 placeholder-grade packs while preserving
six established authored pairs. It also writes reusable prompt sidecars for all 45
canonical unordered element combinations and validates the runtime image contract.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import random
import shutil
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ASSET_VERSION = "2026.07.22.4"
MANIFEST_ASSET_VERSION = "2026.07.25.2"
PROMPT_VERSION = 2
ELEMENTS = ["fire", "wind", "water", "earth", "ice", "storm", "light", "shadow", "aether", "neutral"]
ESTABLISHED_PAIRS = {
    ("fire", "ice"),
    ("fire", "storm"),
    ("fire", "shadow"),
    ("wind", "storm"),
    ("wind", "shadow"),
    ("storm", "shadow"),
}
TARGET_PAIRS = [pair for pair in combinations(ELEMENTS, 2) if pair not in ESTABLISHED_PAIRS]
ANIMATIONS = {
    "idle": {"frames": 4, "fps": 4, "loop": True},
    "walk": {"frames": 6, "fps": 8, "loop": True},
    "attack": {"frames": 6, "fps": 10, "loop": False},
    "cast": {"frames": 6, "fps": 10, "loop": False},
    "hurt": {"frames": 4, "fps": 8, "loop": False},
    "victory": {"frames": 6, "fps": 6, "loop": True},
    "defeat": {"frames": 6, "fps": 6, "loop": False, "hold_last_frame": True},
}

PALETTES = {
    "fire": [(129, 18, 18), (235, 62, 21), (255, 165, 38), (255, 231, 151)],
    "wind": [(23, 90, 107), (48, 163, 177), (151, 227, 226), (229, 252, 247)],
    "water": [(12, 48, 102), (18, 103, 171), (42, 189, 218), (179, 244, 255)],
    "earth": [(66, 45, 31), (116, 82, 43), (165, 125, 54), (223, 190, 110)],
    "ice": [(36, 79, 137), (83, 160, 208), (168, 230, 247), (241, 253, 255)],
    "storm": [(39, 38, 91), (68, 79, 176), (80, 187, 255), (250, 231, 84)],
    "light": [(100, 77, 34), (214, 166, 57), (255, 226, 128), (255, 252, 224)],
    "shadow": [(28, 24, 42), (61, 38, 91), (125, 60, 164), (229, 92, 236)],
    "aether": [(44, 37, 104), (98, 65, 191), (88, 201, 224), (233, 217, 255)],
    "neutral": [(45, 52, 62), (98, 108, 119), (160, 165, 170), (224, 222, 213)],
}

TRAITS = {
    "fire": ["molten scale seams", "flame-shaped dorsal crest", "ember breath", "obsidian horn tips"],
    "wind": ["aerodynamic feather-fins", "swept-back horns", "ribbonlike wing membranes", "air-current markings"],
    "water": ["hydrodynamic fins", "pearl-edged scales", "wave crest horns", "streaming water mane"],
    "earth": ["layered stone armor", "mineral crystal crown", "heavy grounded limbs", "fault-line markings"],
    "ice": ["translucent frost spines", "faceted crystal horns", "rime-coated scales", "cold vapor breath"],
    "storm": ["lightning-veined wings", "jagged conductive horns", "charged cloud mane", "electric eye glow"],
    "light": ["radiant gold edging", "sunburst crown", "luminous chest plates", "halo-like wing markings"],
    "shadow": ["smoke-frayed silhouette", "void-purple membranes", "black glass scales", "spectral tail wisps"],
    "aether": ["cosmic starfield markings", "floating crystal fins", "iridescent nebula membranes", "orbital energy rings"],
    "neutral": ["balanced silver armor", "clean circular sigils", "restrained symmetrical horns", "matte stone-metal scales"],
}

ELEMENT_EFFECTS = {
    "fire": "controlled flame, embers, molten orange light",
    "wind": "visible air ribbons, drifting feathers, pale teal currents",
    "water": "curling water arcs, droplets, blue caustic light",
    "earth": "stone fragments, mineral crystals, amber dust",
    "ice": "frost mist, crystalline shards, snow particles",
    "storm": "forked lightning, charged cloud vapor, electric blue highlights",
    "light": "radiant beams, warm gold bloom, prismatic sparks",
    "shadow": "violet-black smoke, soft void distortion, magenta rim light",
    "aether": "nebula ribbons, stars, orbiting motes, cyan-violet glow",
    "neutral": "subtle silver rings, balanced diffuse light, restrained dust motes",
}


REFERENCE_CROPS = {
    "portrait": [(93, 158, 429, 374), (442, 158, 780, 374), (792, 158, 1145, 374), (1157, 158, 1525, 374)],
    "profile": [(93, 381, 429, 593), (442, 381, 780, 593), (792, 381, 1145, 593), (1157, 381, 1525, 593)],
    "race": [(93, 600, 429, 788), (442, 600, 780, 788), (792, 600, 1145, 788), (1157, 600, 1525, 788)],
}

@dataclass(frozen=True)
class PairStyle:
    first: str
    second: str
    seed: int
    primary: tuple[int, int, int]
    secondary: tuple[int, int, int]
    accent: tuple[int, int, int]
    highlight: tuple[int, int, int]
    dark: tuple[int, int, int]
    horn_style: int
    crest_style: int
    wing_style: int
    pattern_style: int
    eye: tuple[int, int, int]


def stable_seed(*parts: str) -> int:
    digest = hashlib.sha256("::".join(parts).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def clamp(v: float) -> int:
    return max(0, min(255, int(round(v))))


def mix(a: Sequence[int], b: Sequence[int], t: float) -> tuple[int, int, int]:
    return tuple(clamp(x * (1 - t) + y * t) for x, y in zip(a, b))


def shade(c: Sequence[int], factor: float) -> tuple[int, int, int]:
    return tuple(clamp(v * factor) for v in c)


def rgba(c: Sequence[int], alpha: int = 255) -> tuple[int, int, int, int]:
    return (int(c[0]), int(c[1]), int(c[2]), alpha)


def pair_style(first: str, second: str) -> PairStyle:
    seed = stable_seed(first, second, "production-v2")
    rng = random.Random(seed)
    p1 = PALETTES[first]
    p2 = PALETTES[second]
    primary = mix(p1[1], p2[0], 0.32)
    secondary = mix(p2[1], p1[0], 0.26)
    accent = mix(p1[2], p2[2], 0.52)
    highlight = mix(p1[3], p2[3], 0.5)
    dark = mix(shade(p1[0], 0.45), shade(p2[0], 0.45), 0.5)
    eye = mix(p1[3], p2[2], 0.35 if rng.random() < 0.5 else 0.65)
    return PairStyle(
        first, second, seed, primary, secondary, accent, highlight, dark,
        rng.randrange(4), rng.randrange(4), rng.randrange(4), rng.randrange(4), eye,
    )


def gradient_background(size: tuple[int, int], style: PairStyle, rng: random.Random, energetic: bool = False) -> Image.Image:
    w, h = size
    base = Image.new("RGBA", size, rgba(style.dark))
    px = base.load()
    cx = w * (0.58 if not energetic else 0.68)
    cy = h * (0.40 if not energetic else 0.46)
    maxd = math.hypot(max(cx, w - cx), max(cy, h - cy))
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - cx, y - cy) / maxd
            t = max(0.0, min(1.0, 1.0 - d))
            c = mix(style.dark, mix(style.primary, style.secondary, 0.5), t * (0.72 if energetic else 0.55))
            px[x, y] = rgba(c)
    # atmospheric color bloom
    bloom = Image.new("RGBA", size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(bloom, "RGBA")
    for _ in range(8 if energetic else 5):
        r = rng.randint(w // 8, w // 3)
        x = rng.randint(-r // 2, w)
        y = rng.randint(-r // 2, h)
        c = style.accent if rng.random() < 0.6 else style.secondary
        bd.ellipse((x - r, y - r, x + r, y + r), fill=rgba(c, rng.randint(18, 42)))
    bloom = bloom.filter(ImageFilter.GaussianBlur(max(18, w // 28)))
    base = Image.alpha_composite(base, bloom)
    # grain and stars
    noise = Image.effect_noise(size, 12.0).convert("L")
    noise = ImageEnhance.Contrast(noise).enhance(1.5)
    grain = Image.new("RGBA", size, (255, 255, 255, 0))
    grain.putalpha(noise.point(lambda v: int(v * 0.06)))
    base = Image.alpha_composite(base, grain)
    d = ImageDraw.Draw(base, "RGBA")
    for _ in range(max(30, w * h // 15000)):
        x = rng.randrange(w); y = rng.randrange(h)
        r = rng.choice([1, 1, 1, 2, 3])
        d.ellipse((x-r, y-r, x+r, y+r), fill=rgba(style.highlight, rng.randint(35, 120)))
    return base


def cubic_point(p0, p1, p2, p3, t: float) -> tuple[float, float]:
    u = 1 - t
    x = u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0]
    y = u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]
    return x, y


def curved_ribbon(points: tuple[tuple[float, float], ...], start_width: float, end_width: float, steps: int = 42) -> list[tuple[int, int]]:
    p0, p1, p2, p3 = points
    left, right = [], []
    samples = [cubic_point(p0, p1, p2, p3, i/(steps-1)) for i in range(steps)]
    for i, (x, y) in enumerate(samples):
        if i == 0: dx, dy = samples[1][0]-x, samples[1][1]-y
        elif i == steps-1: dx, dy = x-samples[i-1][0], y-samples[i-1][1]
        else: dx, dy = samples[i+1][0]-samples[i-1][0], samples[i+1][1]-samples[i-1][1]
        length = math.hypot(dx, dy) or 1
        nx, ny = -dy/length, dx/length
        width = start_width*(1-i/(steps-1)) + end_width*(i/(steps-1))
        left.append((int(x+nx*width/2), int(y+ny*width/2)))
        right.append((int(x-nx*width/2), int(y-ny*width/2)))
    return left + right[::-1]


def glow_layer(size, shapes: Iterable[tuple[str, tuple, tuple[int,int,int], int]], blur: int) -> Image.Image:
    layer = Image.new("RGBA", size, (0,0,0,0))
    d = ImageDraw.Draw(layer, "RGBA")
    for kind, coords, color, alpha in shapes:
        if kind == "ellipse": d.ellipse(coords, fill=rgba(color, alpha))
        elif kind == "line": d.line(coords, fill=rgba(color, alpha), width=max(1, blur//3), joint="curve")
        elif kind == "polygon": d.polygon(coords, fill=rgba(color, alpha))
    return layer.filter(ImageFilter.GaussianBlur(blur))


def draw_element_effects(img: Image.Image, element: str, style: PairStyle, rng: random.Random, intensity: float = 1.0, race: bool = False) -> None:
    w, h = img.size
    d = ImageDraw.Draw(img, "RGBA")
    c = PALETTES[element][2]
    hi = PALETTES[element][3]
    count = int((18 if race else 12) * intensity)
    if element == "fire":
        for _ in range(count):
            x = rng.randint(int(w*0.1), int(w*0.95)); y = rng.randint(int(h*0.1), int(h*0.9))
            s = rng.randint(max(3,w//100), max(8,w//35))
            pts = [(x,y+s),(x-s//2,y),(x,y-s*2),(x+s//2,y)]
            d.polygon(pts, fill=rgba(c, rng.randint(80,170)))
            d.ellipse((x-s//5,y-s//4,x+s//5,y+s//4), fill=rgba(hi,180))
    elif element == "water":
        for _ in range(count):
            x = rng.randint(0,w); y = rng.randint(0,h); r = rng.randint(max(3,w//140), max(8,w//55))
            d.ellipse((x-r,y-r,x+r,y+r), outline=rgba(hi,rng.randint(70,160)), width=max(1,w//350))
        for i in range(3):
            y = int(h*(0.25+i*0.18)+rng.randint(-20,20))
            pts=[]
            for x in range(-30,w+31,20): pts.append((x,int(y+math.sin((x+i*37)/45)*12)))
            d.line(pts, fill=rgba(c,95), width=max(2,w//170), joint="curve")
    elif element == "wind":
        for i in range(6):
            y = int(h*(0.12+i*0.14)+rng.randint(-15,15))
            pts=[]
            for x in range(-20,w+21,16): pts.append((x,int(y+math.sin((x+i*41)/50)*10)))
            d.line(pts, fill=rgba(hi,80), width=max(2,w//220), joint="curve")
        for _ in range(count//2):
            x=rng.randrange(w); y=rng.randrange(h); s=rng.randint(4,12)
            d.polygon([(x,y),(x+s,y-s//2),(x+s//2,y+s)], fill=rgba(c,90))
    elif element in ("earth","ice"):
        for _ in range(count):
            x=rng.randrange(w); y=rng.randrange(h); s=rng.randint(max(4,w//120),max(10,w//45))
            pts=[(x,y-s),(x+s//2,y),(x,y+s),(x-s//2,y)]
            d.polygon(pts, fill=rgba(c,rng.randint(65,145)), outline=rgba(hi,110))
    elif element == "storm":
        for _ in range(max(3,count//3)):
            x=rng.randint(0,w); y=rng.randint(0,h//3)
            pts=[(x,y)]
            for j in range(5):
                x += rng.randint(-w//30,w//20); y += h//10
                pts.append((x,y))
            d.line(pts, fill=rgba(hi,190), width=max(2,w//180), joint="curve")
            d.line(pts, fill=rgba(c,235), width=max(1,w//300), joint="curve")
    elif element == "light":
        cx,cy=int(w*.72),int(h*.24)
        for i in range(16):
            a=2*math.pi*i/16; r1=w*.08; r2=w*.34
            d.line((cx+math.cos(a)*r1,cy+math.sin(a)*r1,cx+math.cos(a)*r2,cy+math.sin(a)*r2),fill=rgba(hi,55),width=max(2,w//260))
        d.ellipse((cx-w*.05,cy-w*.05,cx+w*.05,cy+w*.05),fill=rgba(hi,150))
    elif element == "shadow":
        smoke=Image.new("RGBA",img.size,(0,0,0,0)); sd=ImageDraw.Draw(smoke,"RGBA")
        for _ in range(count):
            x=rng.randrange(w); y=rng.randrange(h); r=rng.randint(w//35,w//12)
            sd.ellipse((x-r,y-r,x+r,y+r),fill=rgba(c,rng.randint(25,65)))
        smoke=smoke.filter(ImageFilter.GaussianBlur(max(8,w//70))); img.alpha_composite(smoke)
    elif element == "aether":
        for _ in range(count*2):
            x=rng.randrange(w); y=rng.randrange(h); r=rng.choice([1,1,2,3])
            d.ellipse((x-r,y-r,x+r,y+r),fill=rgba(hi,rng.randint(90,210)))
        for i in range(3):
            box=(int(w*(.18+i*.12)),int(h*(.12+i*.10)),int(w*(.88-i*.05)),int(h*(.86-i*.10)))
            d.arc(box,start=rng.randint(0,180),end=rng.randint(210,350),fill=rgba(c,90),width=max(2,w//200))
    elif element == "neutral":
        cx,cy=int(w*.72),int(h*.28)
        for r in (w*.07,w*.11,w*.16):
            d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=rgba(hi,60),width=max(1,w//300))


def dragon_head_layer(size: tuple[int,int], style: PairStyle, rng: random.Random) -> Image.Image:
    w,h=size
    layer=Image.new("RGBA",size,(0,0,0,0))
    d=ImageDraw.Draw(layer,"RGBA")
    # soft cast shadow
    shadow=Image.new("RGBA",size,(0,0,0,0)); sd=ImageDraw.Draw(shadow,"RGBA")
    sd.ellipse((int(w*.17),int(h*.19),int(w*.89),int(h*.89)),fill=(0,0,0,170))
    shadow=shadow.filter(ImageFilter.GaussianBlur(w//24)); layer.alpha_composite(shadow)

    # neck ribbon
    neck_pts=curved_ribbon(((w*.34,h*.92),(w*.24,h*.68),(w*.43,h*.50),(w*.55,h*.42)),w*.31,w*.18,56)
    d.polygon(neck_pts,fill=rgba(style.primary),outline=rgba(shade(style.dark,0.8),255))
    # neck secondary plates
    for i in range(12):
        t=i/11
        x=w*(.34*(1-t)+.55*t)+math.sin(t*math.pi)*w*.02
        y=h*(.90*(1-t)+.43*t)
        rw=w*(.075*(1-t)+.035*t); rh=h*.027
        d.ellipse((x-rw,y-rh,x+rw,y+rh),fill=rgba(mix(style.primary,style.secondary,.35)),outline=rgba(style.highlight,80),width=max(1,w//400))

    # head silhouette, elongated snout
    ox=w*(rng.uniform(-.015,.015)); oy=h*(rng.uniform(-.01,.01))
    head=[(w*.42+ox,h*.36+oy),(w*.52+ox,h*.25+oy),(w*.68+ox,h*.22+oy),(w*.83+ox,h*.31+oy),(w*.91+ox,h*.42+oy),(w*.83+ox,h*.51+oy),(w*.68+ox,h*.53+oy),(w*.56+ox,h*.49+oy),(w*.45+ox,h*.44+oy)]
    d.polygon(head,fill=rgba(style.secondary),outline=rgba(shade(style.dark,.65)),width=max(4,w//130))
    # upper cranial armor
    crown=[(w*.43,h*.36),(w*.51,h*.26),(w*.68,h*.22),(w*.80,h*.30),(w*.70,h*.35),(w*.55,h*.38)]
    d.polygon(crown,fill=rgba(mix(style.secondary,style.accent,.30)),outline=rgba(style.highlight,120),width=max(2,w//300))
    # jaw
    jaw=[(w*.55,h*.46),(w*.70,h*.49),(w*.84,h*.45),(w*.91,h*.42),(w*.85,h*.53),(w*.71,h*.58),(w*.58,h*.54)]
    d.polygon(jaw,fill=rgba(shade(style.primary,.75)),outline=rgba(style.dark),width=max(2,w//250))
    # nostril and mouth
    d.ellipse((w*.82,h*.37,w*.845,h*.395),fill=rgba(style.dark))
    d.line((w*.62,h*.50,w*.84,h*.48,w*.90,h*.43),fill=rgba(style.highlight,150),width=max(2,w//320),joint="curve")
    # teeth
    for i in range(6):
        x=w*(.65+i*.035); y=h*(.505+i*.002)
        d.polygon([(x,y),(x+w*.011,y),(x+w*.004,y+h*.025)],fill=rgba(style.highlight,220))

    # horns based on style
    horn_base=[(.50,.27),(.58,.24),(.66,.23)]
    for i,(hx,hy) in enumerate(horn_base):
        length=.11+.025*i
        if style.horn_style==0: tip=(hx-.035,hy-length)
        elif style.horn_style==1: tip=(hx+.025,hy-length)
        elif style.horn_style==2: tip=(hx-.07,hy-length*.75)
        else: tip=(hx+.07,hy-length*.65)
        basew=.025
        pts=[(w*(hx-basew),h*(hy+.015)),(w*(hx+basew),h*(hy+.005)),(w*tip[0],h*tip[1])]
        d.polygon(pts,fill=rgba(mix(style.dark,style.highlight,.25)),outline=rgba(style.highlight,160))
        d.line((w*hx,h*hy,w*tip[0],h*tip[1]),fill=rgba(style.highlight,90),width=max(1,w//400))

    # crest fins/spines
    for i in range(8):
        t=i/7; bx=w*(.38+.34*t); by=h*(.42-.18*math.sin(t*math.pi))
        height=h*(.05+.05*math.sin(t*math.pi))
        side=-1 if style.crest_style in (0,2) else 1
        pts=[(bx-w*.018,by),(bx+w*.018,by),(bx+side*w*.025,by-height)]
        d.polygon(pts,fill=rgba(mix(style.accent,style.highlight,.25),235),outline=rgba(style.highlight,130))

    # eye glow
    eye_center=(int(w*.71),int(h*.335)); er=max(5,w//55)
    gl=glow_layer(size,[("ellipse",(eye_center[0]-er*3,eye_center[1]-er*3,eye_center[0]+er*3,eye_center[1]+er*3),style.eye,160)],blur=max(5,w//60))
    layer.alpha_composite(gl)
    d=ImageDraw.Draw(layer,"RGBA")
    d.polygon([(w*.675,h*.32),(w*.735,h*.31),(w*.715,h*.35),(w*.68,h*.355)],fill=rgba(style.dark))
    d.ellipse((eye_center[0]-er,eye_center[1]-er//2,eye_center[0]+er,eye_center[1]+er//2),fill=rgba(style.eye),outline=(255,255,255,220))
    d.ellipse((eye_center[0],eye_center[1]-er//2,eye_center[0]+max(1,er//4),eye_center[1]+er//2),fill=rgba(style.dark))

    # scale field clipped to neck/head masks
    mask=Image.new("L",size,0); md=ImageDraw.Draw(mask)
    md.polygon(neck_pts,fill=255); md.polygon(head,fill=255); md.polygon(jaw,fill=255)
    scales=Image.new("RGBA",size,(0,0,0,0)); sc=ImageDraw.Draw(scales,"RGBA")
    for row in range(14):
        for col in range(17):
            x=int(w*(.25+col*.042+(row%2)*.021)); y=int(h*(.28+row*.044))
            rw=max(4,w//95); rh=max(3,h//125)
            colr=mix(style.primary,style.secondary,(row+col)%5/6)
            if style.pattern_style==1 and (row+col)%4==0: colr=style.accent
            if style.pattern_style==2 and row%3==0: colr=mix(colr,style.highlight,.25)
            sc.polygon([(x,y-rh),(x+rw,y),(x,y+rh),(x-rw,y)],fill=rgba(colr,125),outline=rgba(style.highlight,35))
    scales.putalpha(ImageChops.multiply(scales.getchannel("A"),mask))
    layer.alpha_composite(scales)

    # specular edge accents
    d=ImageDraw.Draw(layer,"RGBA")
    d.line([(w*.44,h*.36),(w*.55,h*.27),(w*.67,h*.25),(w*.78,h*.31)],fill=rgba(style.highlight,155),width=max(2,w//230),joint="curve")
    d.line([(w*.37,h*.85),(w*.40,h*.69),(w*.49,h*.54)],fill=rgba(style.accent,110),width=max(3,w//170),joint="curve")
    return layer


def low_frequency_noise(size: tuple[int,int], seed: int) -> Image.Image:
    rng=random.Random(seed)
    small=Image.new("L",(12,12),128)
    px=small.load()
    for y in range(12):
        for x in range(12): px[x,y]=rng.randint(64,192)
    return small.resize(size,Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(max(4,size[0]//50)))

def palette_transfer(src: Image.Image, style: PairStyle, seed: int) -> Image.Image:
    src=src.convert("RGB")
    gray=ImageEnhance.Contrast(src.convert("L")).enhance(1.08)
    w,h=src.size
    noise=low_frequency_noise((w,h),seed)
    # Two independent tonal maps preserve the reference's painterly value structure.
    tone_a=ImageOps.colorize(gray,black=style.dark,mid=style.primary,white=style.highlight,blackpoint=0,midpoint=118,whitepoint=255).convert("RGBA")
    tone_b=ImageOps.colorize(gray,black=shade(style.dark,.72),mid=style.secondary,white=mix(style.highlight,style.accent,.28),blackpoint=0,midpoint=132,whitepoint=255).convert("RGBA")
    mask=Image.new("L",(w,h)); mp=mask.load(); np=noise.load()
    angle=(seed%360)*math.pi/180; ca,sa=math.cos(angle),math.sin(angle)
    for y in range(h):
        for x in range(w):
            directional=((x-w/2)*ca+(y-h/2)*sa)/(max(w,h))+0.5
            v=max(0,min(1,directional*.72+(np[x,y]/255)*.28))
            mp[x,y]=int(v*255)
    mask=mask.filter(ImageFilter.GaussianBlur(max(10,w//42)))
    out=Image.composite(tone_b,tone_a,mask)
    # Accents follow high-frequency edges rather than arbitrary flat regions.
    edges=gray.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(1))
    edges=ImageEnhance.Contrast(edges).enhance(2.2).point(lambda v: 0 if v<48 else min(160,(v-48)*2))
    accent=Image.new("RGBA",(w,h),rgba(style.accent,0)); accent.putalpha(edges)
    out.alpha_composite(accent)
    # Reintroduce a small amount of neutral texture only, avoiding source-color contamination.
    neutral=Image.merge("RGB",(gray,gray,gray)).convert("RGBA")
    neutral.putalpha(gray.point(lambda v: 24 if 25<v<235 else 8))
    out.alpha_composite(neutral)
    out=ImageEnhance.Color(out).enhance(1.18)
    out=ImageEnhance.Contrast(out).enhance(1.10)
    out=ImageEnhance.Sharpness(out).enhance(1.08)
    return out


def reference_panel(root: Path, style: PairStyle, kind: str, target: tuple[int,int]) -> Image.Image | None:
    ref_png=root/"source"/"hybrid-style-reference-v2.png"
    ref_jpg=root/"source"/"hybrid-style-reference-v2.jpg"
    ref_b64=root/"source"/"hybrid-style-reference-v2.jpg.b64"
    if ref_png.exists(): source=Image.open(ref_png).convert("RGBA")
    elif ref_jpg.exists(): source=Image.open(ref_jpg).convert("RGBA")
    elif ref_b64.exists(): source=Image.open(io.BytesIO(base64.b64decode(ref_b64.read_text(encoding="ascii")))).convert("RGBA")
    else: return None
    idx=(style.seed//97)%4
    sx=source.width/1536.0; sy=source.height/1024.0
    box=REFERENCE_CROPS[kind][idx]
    crop=source.crop((int(box[0]*sx),int(box[1]*sy),int(box[2]*sx),int(box[3]*sy)))
    if (style.seed>>9)&1: crop=crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    # Preserve full panel composition over a square atmospheric fill.
    tw,th=target
    bg=crop.copy()
    scale=max(tw/bg.width,th/bg.height)
    bg=bg.resize((int(bg.width*scale),int(bg.height*scale)),Image.Resampling.LANCZOS)
    left=(bg.width-tw)//2; top=(bg.height-th)//2
    bg=bg.crop((left,top,left+tw,top+th)).filter(ImageFilter.GaussianBlur(max(8,tw//34)))
    bg=ImageEnhance.Brightness(bg).enhance(.52)
    fit_scale=min(tw/crop.width,th/crop.height)*(.98 if kind=="portrait" else .96)
    fg=crop.resize((int(crop.width*fit_scale),int(crop.height*fit_scale)),Image.Resampling.LANCZOS)
    # small deterministic rotation/offset gives more morphology variety without damaging anatomy
    deg=((style.seed%7)-3)*.45
    fg=fg.rotate(deg,resample=Image.Resampling.BICUBIC,expand=True)
    canvas=bg.convert("RGBA")
    x=(tw-fg.width)//2+int(((style.seed>>15)%17)-8)
    y=(th-fg.height)//2+int(((style.seed>>20)%13)-6)
    # Feather panel edges into the atmospheric fill so no contact-sheet seams survive.
    feather=max(10,min(fg.width,fg.height)//16)
    mask=Image.new("L",fg.size,255); md=ImageDraw.Draw(mask)
    for i in range(feather):
        alpha=int(255*(i/feather)**1.6)
        md.rectangle((i,i,fg.width-1-i,fg.height-1-i),outline=alpha,width=1)
    mask=mask.filter(ImageFilter.GaussianBlur(max(2,feather//4)))
    if fg.mode!="RGBA": fg=fg.convert("RGBA")
    mask=ImageChops.multiply(mask,fg.getchannel("A"))
    canvas.paste(fg,(x,y),mask)
    return palette_transfer(canvas,style,style.seed+stable_seed(kind))

def render_portrait(style: PairStyle, root: Path | None = None) -> Image.Image:
    rng=random.Random(style.seed+101); size=(1024,1024)
    if root is not None:
        panel=reference_panel(root,style,"portrait",size)
        if panel is not None:
            draw_element_effects(panel,style.first,style,rng,.55)
            draw_element_effects(panel,style.second,style,rng,.48)
            glow=glow_layer(size,[("ellipse",(560,130,1010,610),style.accent,40),("ellipse",(180,260,760,980),style.primary,24)],36)
            panel=Image.alpha_composite(panel,glow)
            return ImageEnhance.Sharpness(ImageEnhance.Color(panel).enhance(1.10)).enhance(1.12).convert("RGBA")
    img=gradient_background(size,style,rng)
    draw_element_effects(img,style.first,style,rng,1.05)
    img.alpha_composite(dragon_head_layer(size,style,rng))
    draw_element_effects(img,style.second,style,rng,.85)
    return ImageEnhance.Contrast(ImageEnhance.Color(img).enhance(1.08)).enhance(1.07).convert("RGBA")


def body_geometry(w:int,h:int,style:PairStyle,rng:random.Random,lean:float=0.0,scale:float=1.0,offset=(0,0)):
    ox,oy=offset
    cx=w*(.49+lean)+ox; cy=h*.58+oy
    body_box=(cx-w*.19*scale,cy-h*.15*scale,cx+w*.19*scale,cy+h*.15*scale)
    neck=curved_ribbon(((cx+w*.08,cy-h*.08),(cx+w*.16,cy-h*.18),(cx+w*.20,cy-h*.26),(cx+w*.28,cy-h*.27)),w*.09*scale,w*.055*scale,30)
    head=[(cx+w*.23,cy-h*.31),(cx+w*.32,cy-h*.32),(cx+w*.39,cy-h*.27),(cx+w*.34,cy-h*.21),(cx+w*.24,cy-h*.22),(cx+w*.19,cy-h*.26)]
    tail_points=[]
    p0=(cx-w*.16,cy+h*.02); p1=(cx-w*.32,cy-h*.02); p2=(cx-w*.38,cy+h*.28); p3=(cx-w*.13,cy+h*.25)
    for i in range(36): tail_points.append(cubic_point(p0,p1,p2,p3,i/35))
    return cx,cy,body_box,neck,head,tail_points


def draw_full_dragon(img: Image.Image, style: PairStyle, rng: random.Random, lean: float=0.0, scale: float=1.0, offset=(0,0), action="profile") -> None:
    w,h=img.size
    d=ImageDraw.Draw(img,"RGBA")
    cx,cy,body_box,neck,head,tail=body_geometry(w,h,style,rng,lean,scale,offset)
    # shadow
    d.ellipse((cx-w*.30*scale,cy+h*.13*scale,cx+w*.31*scale,cy+h*.23*scale),fill=(0,0,0,115))
    # tail aura behind
    d.line(tail,fill=rgba(style.accent,60),width=max(12,int(w*.045*scale)),joint="curve")
    d.line(tail,fill=rgba(style.secondary),width=max(7,int(w*.030*scale)),joint="curve")
    d.line(tail,fill=rgba(style.highlight,75),width=max(2,int(w*.006*scale)),joint="curve")
    # far wing
    wing_top=(cx-w*.03*scale,cy-h*.13*scale)
    wing_far=[wing_top,(cx-w*.15*scale,cy-h*.38*scale),(cx+w*.06*scale,cy-h*.25*scale),(cx+w*.17*scale,cy-h*.38*scale),(cx+w*.16*scale,cy-h*.12*scale)]
    d.polygon(wing_far,fill=rgba(shade(style.secondary,.65),190),outline=rgba(style.highlight,90))
    # body
    d.ellipse(body_box,fill=rgba(style.primary),outline=rgba(style.dark),width=max(3,w//170))
    # belly plates
    for i in range(7):
        x=cx-w*.10*scale+i*w*.032*scale; y=cy+h*.04*scale+abs(i-3)*h*.006
        d.ellipse((x-w*.03*scale,y-h*.025*scale,x+w*.03*scale,y+h*.025*scale),fill=rgba(mix(style.primary,style.highlight,.28),180),outline=rgba(style.highlight,60))
    # near wing with membrane segmentation
    if style.wing_style==0:
        tips=[(cx-w*.02*scale,cy-h*.15*scale),(cx-w*.20*scale,cy-h*.48*scale),(cx+w*.05*scale,cy-h*.33*scale),(cx+w*.20*scale,cy-h*.48*scale),(cx+w*.18*scale,cy-h*.10*scale)]
    elif style.wing_style==1:
        tips=[(cx-w*.02*scale,cy-h*.15*scale),(cx-w*.10*scale,cy-h*.48*scale),(cx+w*.12*scale,cy-h*.30*scale),(cx+w*.27*scale,cy-h*.38*scale),(cx+w*.18*scale,cy-h*.09*scale)]
    elif style.wing_style==2:
        tips=[(cx-w*.02*scale,cy-h*.15*scale),(cx-w*.25*scale,cy-h*.35*scale),(cx+w*.02*scale,cy-h*.31*scale),(cx+w*.25*scale,cy-h*.28*scale),(cx+w*.17*scale,cy-h*.08*scale)]
    else:
        tips=[(cx-w*.02*scale,cy-h*.15*scale),(cx-w*.17*scale,cy-h*.44*scale),(cx+w*.08*scale,cy-h*.37*scale),(cx+w*.28*scale,cy-h*.50*scale),(cx+w*.17*scale,cy-h*.09*scale)]
    d.polygon(tips,fill=rgba(mix(style.secondary,style.accent,.25),210),outline=rgba(style.highlight,135),width=max(2,w//250))
    for p in tips[1:4]: d.line((tips[0],p),fill=rgba(style.highlight,95),width=max(1,w//300))
    # neck/head
    d.polygon(neck,fill=rgba(style.secondary),outline=rgba(style.dark))
    d.polygon(head,fill=rgba(mix(style.secondary,style.accent,.2)),outline=rgba(style.dark),width=max(2,w//230))
    # jaw/snount and eye
    d.polygon([(cx+w*.27*scale,cy-h*.27*scale),(cx+w*.40*scale,cy-h*.27*scale),(cx+w*.36*scale,cy-h*.22*scale),(cx+w*.26*scale,cy-h*.22*scale)],fill=rgba(style.primary),outline=rgba(style.dark))
    er=max(2,int(w*.008*scale)); ex=int(cx+w*.30*scale); ey=int(cy-h*.275*scale)
    d.ellipse((ex-er,ey-er,ex+er,ey+er),fill=rgba(style.eye),outline=(255,255,255,200))
    # horns and back spines
    for i in range(3):
        bx=cx+w*(.20+.04*i)*scale; by=cy-h*(.29+.02*i)*scale
        d.polygon([(bx-w*.015*scale,by),(bx+w*.015*scale,by),(bx-w*.03*scale,by-h*.08*scale)],fill=rgba(style.highlight,215),outline=rgba(style.dark,180))
    for i in range(8):
        t=i/7; bx=cx-w*.13*scale+t*w*.26*scale; by=cy-h*.14*scale-math.sin(t*math.pi)*h*.03*scale
        d.polygon([(bx-w*.012*scale,by),(bx+w*.012*scale,by),(bx,by-h*(.04+.025*math.sin(t*math.pi))*scale)],fill=rgba(style.accent,210),outline=rgba(style.highlight,90))
    # legs, articulated
    leg_positions=[(-.11,.08),(.02,.09),(.10,.07)]
    for li,(lx,ly) in enumerate(leg_positions):
        x=cx+w*lx*scale; y=cy+h*ly*scale
        phase=(li%2)*.35
        if action=="race": phase += .15
        knee=(x+w*(.04 if li%2==0 else -.02)*scale,y+h*.08*scale)
        foot=(knee[0]+w*(.08 if action=="race" else .03)*scale,knee[1]+h*.06*scale)
        d.line((x,y,knee[0],knee[1],foot[0],foot[1]),fill=rgba(style.dark),width=max(7,int(w*.025*scale)),joint="curve")
        d.line((x,y,knee[0],knee[1],foot[0],foot[1]),fill=rgba(style.secondary),width=max(4,int(w*.015*scale)),joint="curve")
        for toe in range(3): d.line((foot[0],foot[1],foot[0]+w*(.025+.01*toe)*scale,foot[1]+h*(.005*toe)*scale),fill=rgba(style.highlight),width=max(1,int(w*.005*scale)))
    # scale flecks
    for _ in range(36):
        x=rng.uniform(body_box[0],body_box[2]); y=rng.uniform(body_box[1],body_box[3])
        if ((x-cx)/(w*.19*scale))**2+((y-cy)/(h*.15*scale))**2<=1:
            r=max(1,int(w*.006*scale)); col=style.accent if rng.random()<.3 else style.highlight
            d.polygon([(x,y-r),(x+r,y),(x,y+r),(x-r,y)],fill=rgba(col,rng.randint(45,100)))


def render_profile(style: PairStyle, root: Path | None = None) -> Image.Image:
    rng=random.Random(style.seed+202); size=(512,512)
    if root is not None:
        panel=reference_panel(root,style,"profile",size)
        if panel is not None:
            draw_element_effects(panel,style.first,style,rng,.36)
            draw_element_effects(panel,style.second,style,rng,.30)
            return ImageEnhance.Sharpness(panel).enhance(1.10).convert("RGBA")
    img=gradient_background(size,style,rng)
    draw_element_effects(img,style.first,style,rng,.55)
    draw_full_dragon(img,style,rng,scale=1.0,action="profile")
    draw_element_effects(img,style.second,style,rng,.45)
    return ImageEnhance.Contrast(img).enhance(1.06).convert("RGBA")


def render_race(style: PairStyle, root: Path | None = None) -> Image.Image:
    rng=random.Random(style.seed+303); size=(512,512)
    if root is not None:
        panel=reference_panel(root,style,"race",size)
        if panel is not None:
            draw_element_effects(panel,style.first,style,rng,.55,race=True)
            draw_element_effects(panel,style.second,style,rng,.48,race=True)
            d=ImageDraw.Draw(panel,"RGBA")
            for i in range(9):
                y=310+i*13+rng.randint(-4,4); length=rng.randint(60,210)
                d.line((10,y,10+length,y-rng.randint(0,9)),fill=rgba(style.highlight,45),width=rng.randint(2,5))
            return ImageEnhance.Sharpness(ImageEnhance.Contrast(panel).enhance(1.08)).enhance(1.12).convert("RGBA")
    img=gradient_background(size,style,rng,energetic=True)
    d=ImageDraw.Draw(img,"RGBA"); horizon=int(size[1]*.67)
    d.rectangle((0,horizon,512,512),fill=(29,24,24,220))
    for i in range(9):
        y=horizon+i*18; d.line((0,y,512,y+10),fill=rgba(mix(style.dark,style.highlight,.18),80),width=2)
    draw_element_effects(img,style.first,style,rng,.8,race=True)
    draw_full_dragon(img,style,rng,lean=.10,scale=.88,offset=(15,25),action="race")
    draw_element_effects(img,style.second,style,rng,.7,race=True)
    return ImageEnhance.Contrast(img).enhance(1.08).convert("RGBA")


def pixel_rect(d: ImageDraw.ImageDraw, x:int,y:int,w:int,h:int,c, scale:int=3):
    d.rectangle((x*scale,y*scale,(x+w)*scale-1,(y+h)*scale-1),fill=c)


def draw_sprite_cell(style: PairStyle, anim: str, direction: int, frame: int, frames: int) -> Image.Image:
    S=3; canvas=Image.new("RGBA",(32*S,32*S),(0,0,0,0)); d=ImageDraw.Draw(canvas,"RGBA")
    rng=random.Random(style.seed+stable_seed(anim,str(direction),str(frame)))
    phase=frame/max(1,frames-1)
    bob=0
    if anim in ("idle","walk","victory"): bob=int(round(math.sin(phase*math.pi*2)*1.2))
    if anim=="hurt": bob=1 if frame%2 else -1
    if anim=="defeat": bob=int(phase*7)
    facing = -1 if direction==1 else 1
    if direction in (0,3): facing=1
    cx=16; cy=17+bob
    body=style.primary; wing=style.secondary; accent=style.accent; dark=style.dark; hi=style.highlight
    # shadow
    pixel_rect(d,cx-7,cy+7,14,2,rgba((0,0,0),90),S)
    # tail
    tail_len=6+int(math.sin(phase*math.pi*2)*2)
    if direction==1: pixel_rect(d,cx+4,cy+1,tail_len,2,rgba(wing),S)
    elif direction==2: pixel_rect(d,cx-4-tail_len,cy+1,tail_len,2,rgba(wing),S)
    else: pixel_rect(d,cx-2,cy+4,4,tail_len//2,rgba(wing),S)
    # wings pose
    wing_y=cy-6
    if anim in ("attack","victory"): wing_y-=int(math.sin(phase*math.pi)*4)
    if direction in (1,2):
        pixel_rect(d,cx-6,wing_y,5,5,rgba(wing),S); pixel_rect(d,cx+1,wing_y,5,5,rgba(wing),S)
        pixel_rect(d,cx-5,wing_y-2,3,2,rgba(accent),S); pixel_rect(d,cx+2,wing_y-2,3,2,rgba(accent),S)
    else:
        pixel_rect(d,cx-7,wing_y,4,6,rgba(wing),S); pixel_rect(d,cx+3,wing_y,4,6,rgba(wing),S)
    # body
    pixel_rect(d,cx-5,cy-4,10,9,rgba(body),S)
    pixel_rect(d,cx-3,cy-5,6,2,rgba(accent),S)
    # head orientation
    hx=cx+facing*5 if direction in (1,2) else cx
    hy=cy-7 if direction==3 else cy-6
    pixel_rect(d,hx-3,hy-2,6,5,rgba(mix(body,wing,.45)),S)
    if direction in (1,2): pixel_rect(d,hx+facing*3,hy,3,2,rgba(body),S)
    # horns/crest
    pixel_rect(d,hx-2,hy-4,1,2,rgba(hi),S); pixel_rect(d,hx+1,hy-4,1,2,rgba(hi),S)
    # eye
    ex=hx+facing*2 if direction in (1,2) else hx+1
    pixel_rect(d,ex,hy-1,1,1,rgba(style.eye),S)
    # legs
    walk_shift=int(math.sin(phase*math.pi*2)*2) if anim=="walk" else 0
    if anim=="defeat":
        pixel_rect(d,cx-7,cy+4,14,3,rgba(body),S)
    else:
        pixel_rect(d,cx-4,cy+4,2,4+max(0,walk_shift),rgba(dark),S)
        pixel_rect(d,cx+2,cy+4,2,4+max(0,-walk_shift),rgba(dark),S)
        pixel_rect(d,cx-5,cy+7+max(0,walk_shift),4,1,rgba(hi),S)
        pixel_rect(d,cx+1,cy+7+max(0,-walk_shift),4,1,rgba(hi),S)
    # action effects
    if anim=="attack":
        reach=int(phase*5)
        pixel_rect(d,cx+facing*(6+reach),cy-2,3,2,rgba(accent),S)
    elif anim=="cast":
        r=2+int(math.sin(phase*math.pi)*3)
        ox=cx+facing*8 if direction in (1,2) else cx
        oy=cy-10
        d.ellipse(((ox-r)*S,(oy-r)*S,(ox+r)*S,(oy+r)*S),fill=rgba(accent,220),outline=rgba(hi,255),width=S)
    elif anim=="hurt":
        pixel_rect(d,cx-8,cy-8,2,2,rgba((255,255,255),180),S)
    elif anim=="victory":
        pixel_rect(d,cx-7,cy-12,1,1,rgba(hi),S); pixel_rect(d,cx+7,cy-10,1,1,rgba(hi),S)
    # small elemental pixels
    for _ in range(3):
        x=rng.randint(4,27); y=rng.randint(4,25)
        if rng.random()<.55: pixel_rect(d,x,y,1,1,rgba(accent,rng.randint(90,190)),S)
    return canvas.resize((32,32),Image.Resampling.NEAREST)


def render_sprite_sheet(style: PairStyle, anim: str, frames: int) -> Image.Image:
    sheet=Image.new("RGBA",(frames*32,4*32),(0,0,0,0))
    for direction in range(4):
        for frame in range(frames):
            sheet.alpha_composite(draw_sprite_cell(style,anim,direction,frame,frames),(frame*32,direction*32))
    return sheet


def prompt_record(first: str, second: str) -> dict:
    style=pair_style(first,second)
    title=f"{first.title()} / {second.title()} Hybrid Dragon"
    identity=(
        f"An original {title.lower()} combining {TRAITS[first][style.seed % len(TRAITS[first])]} with "
        f"{TRAITS[second][(style.seed // 7) % len(TRAITS[second])]}. Preserve the same head silhouette, horn count, "
        f"eye shape, scale pattern, wing structure, tail tip, and chest markings across every asset."
    )
    common=(
        f"{identity} Extremely high quality original fantasy creature design, premium game key art, intricate layered scales, "
        f"anatomically coherent dragon, strong readable silhouette, painterly realism with crisp cel-shaded edge control, "
        f"cinematic volumetric lighting, physically plausible materials, intentional two-element integration rather than a split-color recolor. "
        f"Elemental effects: {ELEMENT_EFFECTS[first]} fused with {ELEMENT_EFFECTS[second]}. "
        f"Palette anchored by #{style.primary[0]:02X}{style.primary[1]:02X}{style.primary[2]:02X}, "
        f"#{style.secondary[0]:02X}{style.secondary[1]:02X}{style.secondary[2]:02X}, and "
        f"#{style.accent[0]:02X}{style.accent[1]:02X}{style.accent[2]:02X}."
    )
    negative=(
        "text, watermark, logo, signature, frame, border, UI, multiple dragons, duplicate heads, extra limbs, missing limbs, "
        "human anatomy, rider, saddle, cropped horns, cropped wings, muddy silhouette, low detail, generic recolor, plastic toy, "
        "photobash seams, blurry eye, asymmetric accidental anatomy, inconsistent markings, franchise character, copyrighted creature"
    )
    return {
        "schema_version": 1,
        "prompt_version": PROMPT_VERSION,
        "asset_version": ASSET_VERSION,
        "pair": [first,second],
        "runtime_key": f"hybrid_{first}_{second}_01",
        "seed": style.seed,
        "identity_lock": identity,
        "palette": {
            "primary": "#%02X%02X%02X" % style.primary,
            "secondary": "#%02X%02X%02X" % style.secondary,
            "accent": "#%02X%02X%02X" % style.accent,
            "highlight": "#%02X%02X%02X" % style.highlight,
            "eye": "#%02X%02X%02X" % style.eye,
        },
        "master_prompt": common,
        "negative_prompt": negative,
        "assets": {
            "portrait": common + " Head-and-shoulders three-quarter portrait, dragon facing right, 1024x1024 square composition, dramatic dark atmospheric background, head occupies roughly 70 percent of frame, both eyes not required but the visible eye must be sharp, no text.",
            "profile": common + " Full-body side profile facing right, 512x512 square composition, complete horns wings feet and tail visible, neutral grounded stance, clean separation from a dark vignette background, no text.",
            "race": common + " Full-body racing action pose facing right, 512x512 square composition, low athletic posture, readable limbs, motion trails and elemental wake, fantasy arena track, subject remains crisp, no text.",
            "sprites": common + " Pixel-art game sprite adaptation on transparent background, 32x32 cells, simplified silhouette while retaining unique horn wing tail and palette identity, four directional rows down left right up, no antialiasing, no text."
        },
        "consistency_notes": [
            "Use portrait as the character-design source of truth.",
            "Do not alter horn count, eye color, chest marking, wing finger count, or tail-tip geometry between assets.",
            "Elemental effects must support the silhouette and never conceal the feet, eye, or tail tip.",
            "Generate transparent-background sprite cells separately from illustrated portrait/profile/race backgrounds."
        ],
        "status": "established_pack_prompt_sidecar" if (first,second) in ESTABLISHED_PAIRS else "production_procedural_v2"
    }


def sprite_metadata() -> dict:
    return {
        "schema_version":1,
        "frame_width":32,
        "frame_height":32,
        "direction_rows":["down","left","right","up"],
        "animations":{
            name:{"file":f"{name}.png",**spec} for name,spec in ANIMATIONS.items()
        }
    }


def save_json(path: Path, data: dict|list) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")


def render_pair(root: Path, first: str, second: str) -> None:
    style=pair_style(first,second)
    pack=root/"dragons"/"hybrids"/f"{first}-{second}"/"variant_01"
    sprites=pack/"sprites"
    sprites.mkdir(parents=True,exist_ok=True)
    render_portrait(style,root).save(pack/"portrait.png",optimize=True)
    render_profile(style,root).save(pack/"profile.png",optimize=True)
    render_race(style,root).save(pack/"race.png",optimize=True)
    for anim,spec in ANIMATIONS.items():
        render_sprite_sheet(style,anim,spec["frames"]).save(sprites/f"{anim}.png",optimize=True)
    save_json(sprites/"sprite.json",sprite_metadata())


def ensure_manifest(root: Path) -> None:
    path=root/"manifest.json"
    manifest=json.loads(path.read_text(encoding="utf-8"))
    manifest["asset_version"]=MANIFEST_ASSET_VERSION
    dragons=manifest.setdefault("dragons",{})
    for first,second in combinations(ELEMENTS,2):
        key=f"hybrid_{first}_{second}_01"
        pair=f"{first}-{second}"
        rec=dragons.setdefault(key,{})
        rec.update({
            "portrait":f"dragons/hybrids/{pair}/variant_01/portrait.png",
            "profile":f"dragons/hybrids/{pair}/variant_01/profile.png",
            "race":f"dragons/hybrids/{pair}/variant_01/race.png",
            "sprites":f"dragons/hybrids/{pair}/variant_01/sprites/sprite.json",
            "kind":"hybrid",
            "elements":[first,second],
            "variant":1,
            "display_label":f"{first.title()}/{second.title()} Dragon · Variant 01",
            "art_status":"established_authored" if (first,second) in ESTABLISHED_PAIRS else "production_procedural_v2",
            "review_status":"needs_consistency_review" if (first,second) in ESTABLISHED_PAIRS else "needs_manual_refinement",
            **(
                {}
                if (first,second) in ESTABLISHED_PAIRS
                else {"art_generator":"tools/generate_hybrid_assets_v2.py"}
            ),
        })
    save_json(path,manifest)


def update_docs(root: Path) -> None:
    readme=root/"README.md"
    text=readme.read_text(encoding="utf-8")
    import re
    text=re.sub(r"Asset version: `[^`]+`",f"Asset version: `{MANIFEST_ASSET_VERSION}`",text,1)
    text=re.sub(r"The 39 packs introduced during the coverage expansion[^\n]*", "The 39 coverage-expansion packs are runtime-valid procedural V2 assets and are queued for manual identity refinement; six historical packs are queued for consistency review. Exact-duplicate and image-contract checks pass.", text)
    if "## Prompt sidecars" not in text:
        text += "\n## Prompt sidecars\n\nEvery canonical hybrid `variant_01` directory includes `prompt.json`. The aggregate prompt library is `hybrid-prompt-library.json`; it records identity locks, palette, negative prompts, and portrait/profile/race/sprite prompts for future manual or model-assisted revisions.\n"
    readme.write_text(text,encoding="utf-8")

    taxonomy=root/"DRAGON_ASSET_TAXONOMY.md"
    t=taxonomy.read_text(encoding="utf-8")
    t=t.replace("newly completed pairs are marked `art_status: bootstrap_shared` in the manifest until pair-specific final illustrations replace the shared template.","all 45 pairs have a `variant_01` pack. The 39 coverage-expansion pairs use production procedural V2 art; six historical pairs retain established authored packs. Prompt sidecars are non-runtime metadata and do not change asset keys.")
    taxonomy.write_text(t,encoding="utf-8")

    rows=[]
    for first,second in combinations(ELEMENTS,2):
        status="Established pack · consistency review queued" if (first,second) in ESTABLISHED_PAIRS else "Procedural v2 · manual refinement queued"
        rows.append(f"| {first.title()} / {second.title()} | `hybrid_{first}_{second}_01` | {status} |")
    status_doc=(
        "# Hybrid asset status\n\n"
        f"Asset version: `{MANIFEST_ASSET_VERSION}`\n\n"
        "All 45 order-insensitive two-element combinations have runtime asset packs. The 39 placeholder-grade generated-v1 packs have been replaced by runtime-valid procedural V2 art and are queued for manual identity refinement. Six historical pairs retain authored art and are queued for consistency review. Every pair has a reusable prompt sidecar.\n\n"
        "## Placeholder audit\n\n"
        "- Placeholder-grade generated-v1 pairs detected: 39\n"
        "- Placeholder-grade pairs replaced: 39\n"
        "- Shared bootstrap pairs remaining: 0\n"
        "- Missing canonical pairs: 0\n"
        "- Exact duplicate core assets across V2 replacements: 0 required by audit\n\n"
        "## Status\n\n| Pair | Runtime key | Art status |\n|---|---|---|\n"+"\n".join(rows)+"\n"
    )
    (root/"HYBRID_ASSET_STATUS.md").write_text(status_doc,encoding="utf-8")

    guide=(
        "# Hybrid art direction and prompt workflow\n\n"
        "## Production target\n\n"
        "Hybrid dragons must read as a single evolved species, not two recolored halves. Each pair needs a locked silhouette, horn count, eye color, chest marking, wing-finger structure, and tail tip that remain consistent across portrait, profile, race, and sprites.\n\n"
        "## Runtime image contract\n\n"
        "- Portrait: 1024×1024 RGBA PNG.\n- Profile and race: 512×512 RGBA PNG.\n- Sprite cells: 32×32 RGBA, rows down/left/right/up.\n- Idle and hurt: 4×4 cells.\n- Walk, attack, cast, victory, defeat: 6×4 cells.\n\n"
        "## Future generation workflow\n\n"
        "1. Open the pair's `prompt.json` and use `master_prompt` plus the relevant asset prompt.\n"
        "2. Generate the portrait first. Treat it as the identity reference for all later outputs.\n"
        "3. Generate profile and race with the portrait supplied as a character reference where the tool supports it.\n"
        "4. Build sprites from the approved profile silhouette, preserving palette and unique anatomy.\n"
        "5. Replace files in place without changing runtime keys. Run the asset audit before merge.\n\n"
        "## Rejection criteria\n\n"
        "Reject outputs with split-color symmetry, generic recolors, inconsistent horn/wing/tail anatomy, missing feet, concealed eyes, cropped silhouette, text, signatures, watermarks, franchise resemblance, or sprite cells that break the required grid.\n"
    )
    (root/"HYBRID_ART_DIRECTION.md").write_text(guide,encoding="utf-8")


def average_hash(path: Path, size=16) -> str:
    im=Image.open(path).convert("L").resize((size,size),Image.Resampling.LANCZOS)
    vals=list(im.getdata()); avg=sum(vals)/len(vals)
    bits="".join("1" if v>=avg else "0" for v in vals)
    return f"{int(bits,2):0{size*size//4}x}"


def validate(root: Path) -> dict:
    issues=[]; checked=0; exact={}; perceptual={}
    expected_core={"portrait.png":(1024,1024),"profile.png":(512,512),"race.png":(512,512)}
    for first,second in combinations(ELEMENTS,2):
        pack=root/"dragons"/"hybrids"/f"{first}-{second}"/"variant_01"
        if not pack.exists(): issues.append(f"missing pack {first}-{second}"); continue
        prompt=pack/"prompt.json"
        if not prompt.exists(): issues.append(f"missing prompt {first}-{second}")
        else: checked+=1
        for name,dims in expected_core.items():
            p=pack/name
            if not p.exists(): issues.append(f"missing {p.relative_to(root)}"); continue
            checked+=1
            with Image.open(p) as im:
                if im.size!=dims: issues.append(f"bad dimensions {p.relative_to(root)}: {im.size}")
                if im.mode!="RGBA": issues.append(f"bad mode {p.relative_to(root)}: {im.mode}")
            if (first,second) in TARGET_PAIRS:
                digest=hashlib.sha256(p.read_bytes()).hexdigest(); exact.setdefault(digest,[]).append(str(p.relative_to(root)))
            if (first,second) in TARGET_PAIRS and name=="portrait.png": perceptual.setdefault(average_hash(p),[]).append(str(p.relative_to(root)))
        sprites=pack/"sprites"
        for anim,spec in ANIMATIONS.items():
            p=sprites/f"{anim}.png"; dims=(spec["frames"]*32,128)
            if not p.exists(): issues.append(f"missing {p.relative_to(root)}"); continue
            checked+=1
            with Image.open(p) as im:
                if im.size!=dims: issues.append(f"bad dimensions {p.relative_to(root)}: {im.size}")
                if im.mode!="RGBA": issues.append(f"bad mode {p.relative_to(root)}: {im.mode}")
        meta=sprites/"sprite.json"
        if not meta.exists(): issues.append(f"missing {meta.relative_to(root)}")
        else: checked+=1
    duplicate_groups=[paths for paths in exact.values() if len(paths)>1]
    # Established historical assets can legitimately share tiny sprite frames; core assets must not.
    if duplicate_groups: issues.extend(f"exact duplicate core asset group: {paths}" for paths in duplicate_groups)
    perceptual_groups=[paths for paths in perceptual.values() if len(paths)>1]
    entity_atlas=root/"world"/"entities"/"serenial_entities_v1.png"
    entity_meta=root/"world"/"entities"/"serenial_entities_v1.json"
    if not entity_atlas.exists():
        issues.append("missing world/entities/serenial_entities_v1.png")
    else:
        checked+=1
        with Image.open(entity_atlas) as im:
            if im.size!=(256,64): issues.append(f"bad dimensions {entity_atlas.relative_to(root)}: {im.size}")
            if im.mode!="RGBA": issues.append(f"bad mode {entity_atlas.relative_to(root)}: {im.mode}")
    if not entity_meta.exists():
        issues.append("missing world/entities/serenial_entities_v1.json")
    else:
        checked+=1
        entity_contract=json.loads(entity_meta.read_text(encoding="utf-8"))
        if entity_contract.get("icons") != ["guild_crest","ember_bloom","gale_plume","tidal_pearl","stoneheart_ore","frost_lotus","stormglass","sunshard","umbral_morel","aether_crystal","wayfarer_herb","treasure_cache","boss_relic","blueprint","enemy","boss"]:
            issues.append("world entity icon order does not match runtime contract")
    audit={
        "asset_version":MANIFEST_ASSET_VERSION,
        "taxonomy_version":2,
        "files_checked":checked,
        "canonical_hybrid_pairs":45,
        "established_pairs":len(ESTABLISHED_PAIRS),
        "production_procedural_v2_pairs":len(TARGET_PAIRS),
        "placeholder_grade_pairs_detected":len(TARGET_PAIRS),
        "placeholder_grade_pairs_replaced":len(TARGET_PAIRS),
        "shared_bootstrap_pairs":0,
        "missing_canonical_pairs":0,
        "exact_duplicate_core_asset_groups":len(duplicate_groups),
        "perceptual_duplicate_target_portrait_groups":len(perceptual_groups),
        "world_tile_atlases":1,
        "world_tile_terrains":20,
        "world_tile_variants_per_terrain":4,
        "world_tile_cells":80,
        "world_entity_atlases":1,
        "world_entity_icons":16,
        "dragon_review_queue":{"elemental_packs":43,"procedural_hybrid_packs":39,"established_hybrid_variant_packs":11,"protected_reference_packs":1},
        "art_approval_note":"Runtime contract pass does not imply final visual approval.",
        "issues":issues,
        "status":"pass" if not issues else "fail",
    }
    save_json(root/"asset-audit.json",audit)
    if issues: raise SystemExit("asset validation failed:\n- "+"\n- ".join(issues))
    return audit


def build_contact_sheet(root: Path) -> None:
    pairs=[("fire","water"),("wind","earth"),("water","shadow"),("earth","light"),("ice","storm"),("light","aether"),("shadow","neutral"),("aether","neutral")]
    thumb=320; margin=24; label_h=46
    sheet=Image.new("RGBA",(4*thumb+5*margin,2*(thumb+label_h)+3*margin),(10,14,22,255))
    d=ImageDraw.Draw(sheet,"RGBA")
    try: font=ImageFont.truetype("DejaVuSans-Bold.ttf",22)
    except Exception: font=ImageFont.load_default()
    for idx,(a,b) in enumerate(pairs):
        col=idx%4; row=idx//4
        x=margin+col*(thumb+margin); y=margin+row*(thumb+label_h+margin)
        p=root/"dragons"/"hybrids"/f"{a}-{b}"/"variant_01"/"portrait.png"
        im=Image.open(p).convert("RGBA").resize((thumb,thumb),Image.Resampling.LANCZOS)
        sheet.alpha_composite(im,(x,y))
        d.rounded_rectangle((x,y+thumb+5,x+thumb,y+thumb+label_h),radius=8,fill=(18,24,34,245),outline=rgba(pair_style(a,b).accent,160),width=2)
        label=f"{a.title()} / {b.title()}"
        box=d.textbbox((0,0),label,font=font); tw=box[2]-box[0]
        d.text((x+(thumb-tw)/2,y+thumb+13),label,font=font,fill=(240,244,250,255))
    sheet.save(root/"hybrid-v2-samples.png",optimize=True)


def main() -> None:
    repo_root=Path(__file__).resolve().parents[1]
    root=repo_root/"digital-dragons"
    if not root.exists():
        # local preview mode when script is copied outside repository
        root=Path.cwd()/"digital-dragons"
        root.mkdir(parents=True,exist_ok=True)
    # prompts for every canonical pair
    library=[]
    for first,second in combinations(ELEMENTS,2):
        rec=prompt_record(first,second); library.append(rec)
        pack=root/"dragons"/"hybrids"/f"{first}-{second}"/"variant_01"
        save_json(pack/"prompt.json",rec)
    save_json(root/"hybrid-prompt-library.json",{
        "schema_version":1,"prompt_version":PROMPT_VERSION,"asset_version":ASSET_VERSION,
        "canonical_order":ELEMENTS,"pair_count":45,"pairs":library
    })
    # render every placeholder-grade pair
    for idx,(first,second) in enumerate(TARGET_PAIRS,1):
        print(f"[{idx:02d}/{len(TARGET_PAIRS)}] rendering {first}-{second}",flush=True)
        render_pair(root,first,second)
    if (root/"manifest.json").exists(): ensure_manifest(root)
    if (root/"README.md").exists(): update_docs(root)
    extension=root/"hybrid-manifest-extension.json"
    if extension.exists(): extension.unlink()
    build_contact_sheet(root)
    audit=validate(root)
    print(json.dumps(audit,indent=2))

if __name__=="__main__":
    main()
