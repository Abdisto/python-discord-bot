{
  pkgs,
  lib,
  config,
  inputs,
  ...
}:
let
  db_user = "discordBot";
  db_name = "discordQuery";
in
{
  packages = with pkgs; [
    git
    postgresql_18
    postgresql_18.pg_config
  ];

  languages.python = {
    enable = true;
    package = pkgs.python314;

    venv.enable = true;

    uv = {
      enable = true;
      sync.enable = true;
    };
  };

  services.postgres = {
    enable = true;
    package = pkgs.postgresql_18;

    initialDatabases = [{ name = db_name; user = db_user; }];

    listen_addresses = "";
  };

  env.DISCORD_BOT_TOKEN = config.secretspec.secrets.DISCORD_BOT_TOKEN;
  env.LAVALINK_HOST = config.secretspec.secrets.LAVALINK_HOST;
  env.LAVALINK_PORT = config.secretspec.secrets.LAVALINK_PORT;
  env.LAVALINK_PASS = config.secretspec.secrets.LAVALINK_PASS;
  env.SONG_PATH = config.secretspec.secrets.SONG_PATH;
  env.PUBLIC_IP = config.secretspec.secrets.PUBLIC_IP;
}
