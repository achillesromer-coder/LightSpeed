"""CGX read-variation probe: reports permitted *candidate* lenses for source bytes.

This is not a semantics oracle. It identifies signatures and parses bounded safe
metadata only, without running executables, extracting archives or opening URLs.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import io
import json
import struct
import zipfile

MAX_PROBE=4*1024*1024
MAX_ZIP_ENTRIES=64

def probe(source: bytes,filename: str='source.bin')->dict:
    suffix=filename.rsplit('.',1)[-1].lower() if '.' in filename else ''
    fmt='opaque-binary';facets=['bytes','source-hash','morton-topology','provenance']
    detail={};evidence='SIGNATURE_ONLY';loss='R0_SOURCE_PRESERVED'
    if source.startswith(b'IWAD') or source.startswith(b'PWAD'):
        fmt='doom-wad'
        if len(source)>=12:
            lumps,offset=struct.unpack_from('<II',source,4)
            valid=(lumps<=2_000_000 and offset+16*lumps<=len(source))
            detail={'lump_count':lumps if valid else 'INVALID', 'directory_in_bounds':valid}
            if valid:facets+=['wad-lump-tree','game-resource-index']
    elif source.startswith(b'\x89PNG\r\n\x1a\n'):
        fmt='png';facets+=['image-preview-if-decoder-available']
        if len(source)>=24 and source[12:16]==b'IHDR':
            width,height=struct.unpack('>II',source[16:24]);detail={'width':width,'height':height,'scale':'pixels; DPI not inferred'}
    elif source.startswith(b'\xff\xd8\xff'):
        fmt='jpeg';facets+=['image-preview-if-decoder-available']
    elif source.startswith(b'%PDF-'):
        fmt='pdf';facets+=['document-viewer-if-installed'];detail={'contents_extracted':False}
    elif source.startswith((b'MZ',b'\x7fELF')):
        fmt='native-executable';facets+=['host-execution-requires-trust-policy'];detail={'execution_authorised':False}
    elif source.startswith(b'PK\x03\x04'):
        fmt='zip-container';facets+=['archive-table-no-extraction']
        try:
            if len(source)<=MAX_PROBE*16:
                with zipfile.ZipFile(io.BytesIO(source)) as z:
                    filenames=z.namelist()[:MAX_ZIP_ENTRIES]
                    detail={'entry_count':len(z.infolist()),'bounded_names':filenames,'archive_content_extracted':False}
                    if '[Content_Types].xml' in z.namelist():
                        fmt='openxml-office-package'
        except (zipfile.BadZipFile,ValueError,RuntimeError):
            detail={'archive':'INCOMPLETE_OR_UNTRUSTED'}
    else:
        if len(source)<=MAX_PROBE:
            try:
                text=source.decode('utf-8')
                if all(c in '\t\n\r' or ord(c)>=32 for c in text):
                    fmt='utf8-text';facets+=['text-native-view']
                    if text.lstrip().startswith(('{','[')):
                        try:
                            parsed=json.loads(text)
                            fmt='json';facets+=['structured-tree']
                            detail={'root_type':type(parsed).__name__,'top_level_count':len(parsed) if hasattr(parsed,'__len__') else None}
                            evidence='BOUNDED_STRUCTURAL_PARSE'
                        except (ValueError,TypeError):pass
                    elif text.lstrip().lower().startswith(('<!doctype html','<html')):
                        fmt='html';facets+=['web-document-sandbox-required'];detail={'script_execution_authorised':False}
                    elif text.lstrip().startswith('<svg'):
                        fmt='svg';facets+=['vector-preview-with-sanitizer'];detail={'active_content_not_trusted':True}
                    elif ',' in text.splitlines()[0] if text.splitlines() else False:
                        fmt='possible-csv';facets+=['table-parse-unverified']
            except UnicodeDecodeError:pass
    return {'source_sha256':hashlib.sha256(source).hexdigest(),'original_name_hint':filename,
        'length_bytes':len(source),'read_mode':fmt,'facets':facets,'metadata':detail,
        'evidence':evidence,'preservation':loss,
        'semantic_identity_inferred':False,'application_execution_authorized':False,
        'licence_or_owner_verified':False,'source_bytes_needed_for_R0':True}


def section_svg_preview(view: dict, *, preview_authorised: bool = False,
                        canvas: int = 800, padding: int = 32) -> str:
    """Bounded *static* SVG preview from an upstream 2D section/silhouette.

    Caller must enforce original FileSpace ACL, rights, permitted visibility
    and source/DBR checks. No source metadata is embedded in the output.
    This neither talks to a printer nor authorises publication or toolpaths.
    """
    import math
    if preview_authorised is not True:
        raise ValueError('Independent caller preview permission required')
    if type(canvas) is not int or not 128 <= canvas <= 4096:
        raise ValueError('Invalid SVG canvas')
    if type(padding) is not int or not 0 <= padding < canvas//3:
        raise ValueError('Invalid SVG padding')
    if not isinstance(view,dict) or view.get('kind') not in (
        'EMPTY','POINT','SEGMENT','POLYGON'
    ) or view.get('mode') not in ('section','projection'):
        raise ValueError('Invalid geometry view for static preview')
    xy=view.get('points_2d')
    if not isinstance(xy,(list,tuple)) or len(xy)>512:
        raise ValueError('Invalid or oversized 2D polygon')
    points=[]
    for pt in xy:
        if not isinstance(pt,(tuple,list)) or len(pt)!=2 or any(
            type(v) not in (int,float) or not math.isfinite(v) for v in pt
        ):
            raise ValueError('Nonfinite 2D point')
        points.append((float(pt[0]),float(pt[1])))
    expected={'EMPTY':0,'POINT':1,'SEGMENT':2}
    if view['kind'] in expected and len(points)!=expected[view['kind']]:
        raise ValueError('Geometry cardinality mismatch')
    if view['kind']=='POLYGON' and len(points)<3:
        raise ValueError('Polygon needs at least 3 points')
    head=(f'<svg xmlns="http://www.w3.org/2000/svg" '
          f'width="{canvas}" height="{canvas}" viewBox="0 0 {canvas} {canvas}" '
          f'role="img" aria-label="Bounded geometric preview">')
    foot='</svg>'
    if not points:
        return head+foot
    minx,maxx=min(p[0] for p in points),max(p[0] for p in points)
    miny,maxy=min(p[1] for p in points),max(p[1] for p in points)
    span=max(maxx-minx,maxy-miny,1e-12)
    scale=(canvas-2*padding)/span
    coords=[(canvas/2+(x-(minx+maxx)/2)*scale,
             canvas/2-(y-(miny+maxy)/2)*scale) for x,y in points]
    d='M '+' L '.join(f'{x:.6f},{y:.6f}' for x,y in coords)
    if view['kind']=='POLYGON':
        d+=' Z'
    if view['kind']=='POINT':
        x,y=coords[0]
        glyph=(f'<circle cx="{x:.6f}" cy="{y:.6f}" r="3" fill="#222222"/>')
    else:
        glyph=(f'<path d="{d}" fill="none" stroke="#222222" '
               f'stroke-width="1.5" stroke-linejoin="round"/>')
    return head+glyph+foot
