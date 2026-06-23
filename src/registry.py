"""Single source of truth: ordered map of output filename -> bilingual content."""
import part1
import part2
import part3

CONTENT = {
    "01-why-agent-memory.html": part1.LESSON_01,
    "02-one-conversation-flow.html": part1.LESSON_02,
    "03-two-memory-spines.html": part1.LESSON_03,
    "04-openclaw-zero-config.html": part2.LESSON_04,
    "05-hermes-gateway-path.html": part2.LESSON_05,
    "06-runtime-files.html": part2.LESSON_06,
    "07-config-levels.html": part2.LESSON_07,
    "08-openclaw-plugin-shell.html": part3.LESSON_08,
    "09-tdai-core-facade.html": part3.LESSON_09,
    "10-host-adapter-boundaries.html": part3.LESSON_10,
}
