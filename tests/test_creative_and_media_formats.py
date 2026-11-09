"""
Tests for Creative, 3D, Video Editing, Game Development, and Media Player formats:
Photoshop, Illustrator, After Effects, Premiere Pro, DaVinci Resolve, Blender, Unity,
Video Players, CapCut, and related ecosystem formats.
"""

import gzip
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path
from bytesift.core.classifier import Classifier
from bytesift.inspectors.magic_bytes import inspect_magic_bytes
from bytesift.inspectors.text_heuristics import inspect_text_content

class TestCreativeAndMediaFormats(unittest.TestCase):
    def setUp(self):
        self.classifier = Classifier()

    # 1. Photoshop
    def test_photoshop_psd_magic_bytes(self):
        with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as f:
            # 8BPS header without .psd extension
            f.write(b"8BPS\x00\x01\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x01\x00")
            path = Path(f.name)
        try:
            result = self.classifier.classify(path)
            self.assertEqual(result.category, "Design")
            self.assertEqual(result.subcategory, "Photoshop")
            self.assertEqual(result.folder_path, "Design/Photoshop")
            self.assertEqual(result.method, "magic_bytes")
        finally:
            path.unlink()

    def test_photoshop_extensions(self):
        for ext in (".psd", ".psb", ".abr", ".atn", ".pat"):
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                f.write(b"arbitrary bytes")
                path = Path(f.name)
            try:
                result = self.classifier.classify(path)
                self.assertEqual(result.category, "Design")
                self.assertEqual(result.subcategory, "Photoshop")
            finally:
                path.unlink()

    # 2. Illustrator
    def test_illustrator_ai_with_pdf_header(self):
        with tempfile.NamedTemporaryFile(suffix=".ai", delete=False) as f:
            f.write(b"%PDF-1.5\n%Adobe Illustrator Private Data\n")
            path = Path(f.name)
        try:
            result = self.classifier.classify(path)
            self.assertEqual(result.category, "Design")
            self.assertEqual(result.subcategory, "Illustrator")
            self.assertEqual(result.folder_path, "Design/Illustrator")
        finally:
            path.unlink()

    def test_illustrator_magic_without_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as f:
            f.write(b"%PDF-1.4\n%%Creator: Adobe Illustrator CS6\n<</AIPrivateData ...>>")
            path = Path(f.name)
        try:
            result = self.classifier.classify(path)
            self.assertEqual(result.category, "Design")
            self.assertEqual(result.subcategory, "Illustrator")
        finally:
            path.unlink()

    # 3. After Effects
    def test_after_effects_aep_riff_magic(self):
        with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as f:
            # RIFF container with FourCC Egg! (After Effects Project)
            f.write(b"RIFF\x20\x00\x00\x00Egg!data1234567890")
            path = Path(f.name)
        try:
            result = self.classifier.classify(path)
            self.assertEqual(result.category, "Video_Projects")
            self.assertEqual(result.subcategory, "After_Effects")
            self.assertEqual(result.folder_path, "Video_Projects/After_Effects")
        finally:
            path.unlink()

    def test_after_effects_aepx_xml(self):
        with tempfile.NamedTemporaryFile(suffix=".aepx", delete=False) as f:
            f.write(b"<?xml version=\"1.0\"?>\n<AfterEffectsProject version=\"17.0\">\n<Composition .../>\n</AfterEffectsProject>")
            path = Path(f.name)
        try:
            result = self.classifier.classify(path)
            self.assertEqual(result.category, "Video_Projects")
            self.assertEqual(result.subcategory, "After_Effects")
        finally:
            path.unlink()

    # 4. Premiere Pro
    def test_premiere_pro_prproj_gzip_magic(self):
        with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as f:
            # Gzip-compressed XML with PremiereData
            content = gzip.compress(b"<?xml version=\"1.0\"?>\n<PremiereData Version=\"3\">\n<Project ObjectID=\"1\"/></PremiereData>")
            f.write(content)
            path = Path(f.name)
        try:
            result = self.classifier.classify(path)
            self.assertEqual(result.category, "Video_Projects")
            self.assertEqual(result.subcategory, "Premiere_Pro")
            self.assertEqual(result.folder_path, "Video_Projects/Premiere_Pro")
        finally:
            path.unlink()

    def test_premiere_pro_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".prproj", delete=False) as f:
            f.write(b"some content")
            path = Path(f.name)
        try:
            result = self.classifier.classify(path)
            self.assertEqual(result.category, "Video_Projects")
            self.assertEqual(result.subcategory, "Premiere_Pro")
        finally:
            path.unlink()

    # 5. DaVinci Resolve
    def test_davinci_resolve_drp_zip(self):
        with tempfile.NamedTemporaryFile(suffix=".drp", delete=False) as f:
            with zipfile.ZipFile(f, "w") as z:
                z.writestr("project.xml", "<Sm2Project><ResolveVersion>18.6</ResolveVersion></Sm2Project>")
            path = Path(f.name)
        try:
            result = self.classifier.classify(path)
            self.assertEqual(result.category, "Video_Projects")
            self.assertEqual(result.subcategory, "DaVinci_Resolve")
            self.assertEqual(result.folder_path, "Video_Projects/DaVinci_Resolve")
        finally:
            path.unlink()

    def test_davinci_resolve_zip_without_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as f:
            with zipfile.ZipFile(f, "w") as z:
                z.writestr("project.xml", "<Sm2Project><ResolveVersion>18.6</ResolveVersion></Sm2Project>")
            path = Path(f.name)
        try:
            result = self.classifier.classify(path)
            self.assertEqual(result.category, "Video_Projects")
            self.assertEqual(result.subcategory, "DaVinci_Resolve")
        finally:
            path.unlink()

    # 6. Blender
    def test_blender_magic_bytes(self):
        with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as f:
            f.write(b"BLENDER_v400someblendermodeldata")
            path = Path(f.name)
        try:
            result = self.classifier.classify(path)
            self.assertEqual(result.category, "3D_Models")
            self.assertEqual(result.subcategory, "Blender")
            self.assertEqual(result.folder_path, "3D_Models/Blender")
        finally:
            path.unlink()

    def test_blender_extension(self):
        for ext in (".blend", ".blend1", ".blend2"):
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                f.write(b"test data")
                path = Path(f.name)
            try:
                result = self.classifier.classify(path)
                self.assertEqual(result.category, "3D_Models")
                self.assertEqual(result.subcategory, "Blender")
            finally:
                path.unlink()

    # 7. Unity
    def test_unity_binary_asset_magic(self):
        with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as f:
            f.write(b"UnityFS\x00\x00\x00\x065.x.x\x00")
            path = Path(f.name)
        try:
            result = self.classifier.classify(path)
            self.assertEqual(result.category, "Game_Development")
            self.assertEqual(result.subcategory, "Unity")
            self.assertEqual(result.folder_path, "Game_Development/Unity")
        finally:
            path.unlink()

    def test_unity_yaml_scene(self):
        with tempfile.NamedTemporaryFile(suffix=".unity", delete=False) as f:
            f.write(b"%YAML 1.1\n%TAG !u! tag:unity3d.com,2011:\n--- !u!29 &1\nOcclusionCullingSettings:\n  m_ObjectHideFlags: 0\n")
            path = Path(f.name)
        try:
            result = self.classifier.classify(path)
            self.assertEqual(result.category, "Game_Development")
            self.assertEqual(result.subcategory, "Unity")
        finally:
            path.unlink()

    def test_unity_package_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".unitypackage", delete=False) as f:
            f.write(gzip.compress(b"unitypackage content"))
            path = Path(f.name)
        try:
            result = self.classifier.classify(path)
            self.assertEqual(result.category, "Game_Development")
            self.assertEqual(result.subcategory, "Unity")
        finally:
            path.unlink()

    # 8. Video Players & Video Media Formats
    def test_video_quicktime_mov(self):
        with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as f:
            # ftyp with brand qt
            f.write(b"\x00\x00\x00\x14ftypqt  \x00\x00\x00\x00qt  ")
            path = Path(f.name)
        try:
            result = self.classifier.classify(path)
            self.assertEqual(result.category, "Videos")
            self.assertEqual(result.subcategory, "MOV")
            self.assertEqual(result.folder_path, "Videos/MOV")
        finally:
            path.unlink()

    def test_video_wmv_magic(self):
        with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as f:
            # ASF / WMV header GUID
            f.write(b"\x30\x26\xb2\x75\x8e\x66\xcf\x11\xa6\xd9\x00\xaa\x00\x62\xce\x6c\x00\x00")
            path = Path(f.name)
        try:
            result = self.classifier.classify(path)
            self.assertEqual(result.category, "Videos")
            self.assertEqual(result.subcategory, "WMV")
            self.assertEqual(result.folder_path, "Videos/WMV")
        finally:
            path.unlink()

    def test_video_mkv_and_webm(self):
        # MKV
        with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as f:
            f.write(b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01matroska")
            path_mkv = Path(f.name)
        try:
            res_mkv = self.classifier.classify(path_mkv)
            self.assertEqual(res_mkv.category, "Videos")
            self.assertEqual(res_mkv.subcategory, "MKV")
        finally:
            path_mkv.unlink()

        # WebM
        with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as f:
            f.write(b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01webm")
            path_webm = Path(f.name)
        try:
            res_webm = self.classifier.classify(path_webm)
            self.assertEqual(res_webm.category, "Videos")
            self.assertEqual(res_webm.subcategory, "WebM")
        finally:
            path_webm.unlink()

    def test_video_subtitles_and_playlists(self):
        # Subtitle SRT
        with tempfile.NamedTemporaryFile(suffix=".srt", delete=False) as f:
            f.write(b"1\n00:00:01,000 --> 00:00:04,000\nHello, welcome to ByteSift!\n\n")
            path_srt = Path(f.name)
        try:
            res_srt = self.classifier.classify(path_srt)
            self.assertEqual(res_srt.category, "Videos")
            self.assertEqual(res_srt.subcategory, "Subtitles")
        finally:
            path_srt.unlink()

        # Playlist M3U
        with tempfile.NamedTemporaryFile(suffix=".m3u", delete=False) as f:
            f.write(b"#EXTM3U\n#EXTINF:123,Song Name\nsong.mp3\n")
            path_m3u = Path(f.name)
        try:
            res_m3u = self.classifier.classify(path_m3u)
            self.assertEqual(res_m3u.category, "Videos")
            self.assertEqual(res_m3u.subcategory, "Playlists")
        finally:
            path_m3u.unlink()

    # 9. CapCut
    def test_capcut_draft_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            f.write(b'{"draft_id": "12345", "draft_materials": [], "canvas_config": {"width": 1920, "height": 1080}, "capcut_version": "3.5"}')
            path = Path(f.name)
        try:
            result = self.classifier.classify(path)
            self.assertEqual(result.category, "Video_Projects")
            self.assertEqual(result.subcategory, "CapCut")
            self.assertEqual(result.folder_path, "Video_Projects/CapCut")
        finally:
            path.unlink()

    def test_capcut_extension(self):
        for ext in (".capcut", ".ccproj"):
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                f.write(b"capcut draft project data")
                path = Path(f.name)
            try:
                result = self.classifier.classify(path)
                self.assertEqual(result.category, "Video_Projects")
                self.assertEqual(result.subcategory, "CapCut")
            finally:
                path.unlink()

    # 10. Related Ecosystem Formats (InDesign, Figma, FBX, FL Studio)
    def test_indesign_figma_fbx_flstudio(self):
        # InDesign GUID
        with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as f:
            f.write(b"\x06\x06\xed\xf5\xd8\x1d\x46\xe5\xbd\x31\xef\xe7\xfe\x74\xb7\x1dsomeindesigncontent")
            path_id = Path(f.name)
        try:
            res_id = self.classifier.classify(path_id)
            self.assertEqual(res_id.category, "Design")
            self.assertEqual(res_id.subcategory, "InDesign")
        finally:
            path_id.unlink()

        # Figma
        with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as f:
            f.write(b"fig-kiwi\x00\x00\x00\x01somefigmadata")
            path_fig = Path(f.name)
        try:
            res_fig = self.classifier.classify(path_fig)
            self.assertEqual(res_fig.category, "Design")
            self.assertEqual(res_fig.subcategory, "Figma")
        finally:
            path_fig.unlink()

        # FBX
        with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as f:
            f.write(b"Kaydara FBX Binary  \x00\x1a\x00somefbxdata")
            path_fbx = Path(f.name)
        try:
            res_fbx = self.classifier.classify(path_fbx)
            self.assertEqual(res_fbx.category, "3D_Models")
            self.assertEqual(res_fbx.subcategory, "FBX")
        finally:
            path_fbx.unlink()

        # FL Studio
        with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as f:
            f.write(b"FLhd\x06\x00\x00\x00\x01\x00")
            path_flp = Path(f.name)
        try:
            res_flp = self.classifier.classify(path_flp)
            self.assertEqual(res_flp.category, "Audio_Projects")
            self.assertEqual(res_flp.subcategory, "FL_Studio")
        finally:
            path_flp.unlink()

if __name__ == "__main__":
    unittest.main()
