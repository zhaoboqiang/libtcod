
#include "sdl2_alias.h"

#include <map>
#include <memory>
#include <stdexcept>
#include <tuple>

#include <SDL.h>
namespace tcod {
namespace sdl2 {
std::map<std::tuple<const Tileset*, const struct SDL_Renderer*>,
         std::shared_ptr<SDL2InternalTilesetAlias_>> sdl2_alias_pool = {};

class SDL2InternalTilesetAlias_: public TilesetObserver {
 public:
  using key_type = std::tuple<const Tileset*, const struct SDL_Renderer*>;
  SDL2InternalTilesetAlias_(std::shared_ptr<Tileset>& tileset,
                           struct SDL_Renderer* sdl2_renderer)
  : TilesetObserver(tileset), renderer_(sdl2_renderer)
  {
    if (!renderer_) {
      throw std::invalid_argument("sdl2_renderer cannot be nullptr.");
    }
    sync_alias();
  }
  SDL_Texture* get_texture_alias()
  {
    return texture_;
  }
 protected:
  virtual void on_tileset_changed(
      const std::vector<std::pair<int, Tile&>> &changes) override
  {
    sync_alias();
  }
 private:
  void clear_alias()
  {
    if (texture_) { SDL_DestroyTexture(texture_); }
    texture_ = nullptr;
  }
  void sync_alias()
  {
    clear_alias();
    const std::vector<Tile>& tiles = get_tileset().get_tiles();
    int tile_width = get_tileset().get_tile_width();
    int tile_height = get_tileset().get_tile_height();
    int width = tile_width * tiles.size();
    int height = tile_height;
    texture_ = SDL_CreateTexture(renderer_, SDL_PIXELFORMAT_RGBA32,
                                 SDL_TEXTUREACCESS_STATIC, width, height);
    Canvas alias(width, height);
    for (size_t i = 0; i < tiles.size(); ++i) {
      Canvas tile = tiles.at(i).get_image();
      for (int y = 0; y < tile_height; ++y) {
        for (int x = 0; x < tile_width; ++x) {
          alias.at(x + tile_width * i, y) = tile.at(x, y);
        }
      }
    }
    SDL_UpdateTexture(texture_, nullptr, alias.data(),
                      sizeof(alias.at(0,0)) * alias.width());
  }
  struct SDL_Renderer* renderer_;
  struct SDL_Texture* texture_;
};

SDL2TilesetAlias::SDL2TilesetAlias(std::shared_ptr<Tileset>& tileset,
                                   struct SDL_Renderer* sdl2_renderer)
{
  SDL2InternalTilesetAlias_::key_type key =
      std::make_tuple(tileset.get(), sdl2_renderer);
  auto alias_it = sdl2_alias_pool.find(key);
  if (alias_it == sdl2_alias_pool.end()) {
    alias_it = sdl2_alias_pool.emplace(
        key,
        std::make_shared<SDL2InternalTilesetAlias_>(tileset,
                                                    sdl2_renderer)).first;
  }
  alias_ = alias_it->second;
}

} // namespace sdl2
} // namespace tcod
