import unittest
import os
import tempfile
import shutil
import yaml
from lisa.commands import resolve_skill_path, _SKILL_BASE

class TestSkillResolution(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = os.path.join(self.test_dir, "project")
        os.makedirs(self.project_root)
        
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _write_config(self, config_dict):
        lisa_dir = os.path.join(self.project_root, ".lisa")
        if not os.path.exists(lisa_dir):
            os.makedirs(lisa_dir)
        with open(os.path.join(lisa_dir, "config.yaml"), "w") as f:
            yaml.dump(config_dict, f)

    def test_resolve_skill_path_default(self):
        """Should resolve to .lisa/skills by default if file exists."""
        skills_dir = os.path.join(self.project_root, ".lisa", "skills")
        os.makedirs(skills_dir)
        skill_file = os.path.join(skills_dir, "test.md")
        with open(skill_file, "w") as f:
            f.write("test content")
            
        path = resolve_skill_path(self.project_root, "test.md", "some/internal.md")
        self.assertEqual(path, skill_file)

    def test_resolve_skill_path_custom_relative(self):
        """Should resolve to a custom relative path."""
        self._write_config({"skill_base_path": "custom/skills"})
        skills_dir = os.path.join(self.project_root, "custom", "skills")
        os.makedirs(skills_dir)
        skill_file = os.path.join(skills_dir, "test.md")
        with open(skill_file, "w") as f:
            f.write("test content")
            
        path = resolve_skill_path(self.project_root, "test.md", "some/internal.md")
        self.assertEqual(path, skill_file)

    def test_resolve_skill_path_placeholder(self):
        """Should support {project-root} placeholder."""
        self._write_config({"skill_base_path": "{project-root}/abs/skills"})
        skills_dir = os.path.join(self.project_root, "abs", "skills")
        os.makedirs(skills_dir)
        skill_file = os.path.join(skills_dir, "test.md")
        with open(skill_file, "w") as f:
            f.write("test content")
            
        path = resolve_skill_path(self.project_root, "test.md", "some/internal.md")
        self.assertEqual(path, skill_file)

    def test_resolve_skill_path_fallback(self):
        """Should fall back to internal if local does not exist."""
        path = resolve_skill_path(self.project_root, "nonexistent.md", "polish-pass/skill.md")
        expected = os.path.join(_SKILL_BASE, "polish-pass/skill.md")
        self.assertEqual(path, expected)

if __name__ == "__main__":
    unittest.main()
