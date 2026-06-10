/* global React, TweaksPanel, TweakSection, TweakColor, TweakRadio, TweakSelect, TweakToggle, useTweaks */

const DEFAULTS = /*EDITMODE-BEGIN*/{
  "accentHue": 200,
  "density": "normal",
  "fontSans": "Inter",
  "fontMono": "JetBrains Mono",
  "animate": true,
  "showAgentRail": true,
  "defaultTheme": "light"
}/*EDITMODE-END*/;

function AppTweaks() {
  const [t, setTweak] = useTweaks(DEFAULTS);

  React.useEffect(() => {
    const r = document.documentElement;
    r.style.setProperty("--accent-hue", t.accentHue);
    r.style.setProperty(
      "--density",
      t.density === "compact" ? "0.88" : t.density === "spacious" ? "1.12" : "1"
    );
    r.style.setProperty("--font-sans", `"${t.fontSans}", system-ui, sans-serif`);
    r.style.setProperty("--font-mono", `"${t.fontMono}", ui-monospace, monospace`);
    // expose to react world (read by variants for rail toggle)
    window.__tweaks = t;
    // notify variants
    window.dispatchEvent(new CustomEvent("tweaks-changed", { detail: t }));
  }, [t]);

  return (
    <TweaksPanel title="Tweaks · UI">
      <TweakSection label="Accent · 강조 색">
        <TweakColor
          label="hue"
          value={`oklch(0.6 0.16 ${t.accentHue})`}
          options={[
            "oklch(0.6 0.16 200)",  // cyan-teal (default)
            "oklch(0.6 0.16 270)",  // indigo
            "oklch(0.6 0.16 340)",  // magenta
            "oklch(0.65 0.16 50)",  // amber
            "oklch(0.58 0.15 140)", // green
            "oklch(0.6 0.18 0)",    // red
          ]}
          onChange={v => {
            const m = v.match(/(\d+(?:\.\d+)?)\)/);
            if (m) setTweak("accentHue", parseFloat(m[1]));
          }}
        />
      </TweakSection>

      <TweakSection label="Density · 정보 밀도">
        <TweakRadio
          label="density"
          value={t.density}
          options={["compact", "normal", "spacious"]}
          onChange={v => setTweak("density", v)}
        />
      </TweakSection>

      <TweakSection label="Typography">
        <TweakSelect
          label="sans"
          value={t.fontSans}
          options={["Inter", "IBM Plex Sans", "Geist", "Space Grotesk", "DM Sans"]}
          onChange={v => setTweak("fontSans", v)}
        />
        <TweakSelect
          label="mono"
          value={t.fontMono}
          options={["JetBrains Mono", "IBM Plex Mono", "Geist Mono", "Space Mono", "DM Mono"]}
          onChange={v => setTweak("fontMono", v)}
        />
      </TweakSection>

      <TweakSection label="Behavior">
        <TweakToggle
          label="Animate pipeline"
          value={t.animate}
          onChange={v => setTweak("animate", v)}
        />
        <TweakToggle
          label="Show 5-agent rail (A)"
          value={t.showAgentRail}
          onChange={v => setTweak("showAgentRail", v)}
        />
        <TweakSelect
          label="Default theme"
          value={t.defaultTheme}
          options={["light", "dark"]}
          onChange={v => setTweak("defaultTheme", v)}
        />
      </TweakSection>
    </TweaksPanel>
  );
}

// Override TweakColor's display: since hue is a number, render swatch from it
// We monkey-patch the swatch render to use the hue value if it's numeric.
// Simpler: present hue choices through a custom inline UI to override visuals.
// Approach: replace TweakColor's swatch by intercepting render — skip and write a small helper.

function HueSwatchPicker({ value, onChange, hues = [200, 270, 340, 50, 140, 0] }) {
  return (
    <div style={{ display: "flex", gap: 4 }}>
      {hues.map(h => (
        <button key={h} onClick={() => onChange(h)} title={`hue ${h}°`}
          style={{
            width: 22, height: 22, borderRadius: 4, cursor: "pointer",
            background: `oklch(0.58 0.15 ${h})`,
            border: value === h ? "2px solid var(--text)" : "1px solid var(--border)",
            padding: 0,
          }} />
      ))}
    </div>
  );
}

window.AppTweaks = AppTweaks;
window.HueSwatchPicker = HueSwatchPicker;
