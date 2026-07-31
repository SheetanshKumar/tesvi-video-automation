/**
 * Renderer — Cloud Run Job entrypoint.
 *
 * Invoked with RENDER_ID pointing at a row in the `renders` table.
 * Real flow (per docs/ARCHITECTURE.md §3.6): pull render row →
 * synthesize TTS → render frames via Remotion → mux with ffmpeg →
 * upload mp4+thumbnail+captions to GCS → update `renders` row →
 * publish render.completed.
 *
 * This scaffold logs the args and exits.
 */

const serviceName = "renderer";

function log(
  level: "info" | "error",
  msg: string,
  fields: Record<string, unknown> = {},
): void {
  process.stdout.write(
    JSON.stringify({
      ts: new Date().toISOString(),
      level,
      service: serviceName,
      msg,
      ...fields,
    }) + "\n",
  );
}

async function main(): Promise<void> {
  const renderId = process.env.RENDER_ID;
  if (!renderId) {
    log("error", "RENDER_ID env var is required");
    process.exit(2);
  }
  log("info", "renderer invoked", { renderId });
  // TODO: real render pipeline lands with Remotion + Google Cloud TTS + ffmpeg.
  log("info", "renderer completed (skeleton only)", { renderId });
}

main().catch((err: unknown) => {
  log("error", "renderer crashed", { err: String(err) });
  process.exit(1);
});
