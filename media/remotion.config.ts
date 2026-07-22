// Remotion CLI/studio config. See https://remotion.dev/docs/config

import { Config } from "@remotion/cli/config";

// The promo embeds the recorded example clips (table/hss/piston) via
// staticFile(); they live beside the promo output in docs/public.
Config.setPublicDir("../docs/public");

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
