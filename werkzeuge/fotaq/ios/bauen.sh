#!/bin/bash
# MoveEye (FOTAQ, iPhone test): builds ONE test variant of ScummVM (only the Queen engine) and measures its functions.
#   bauen.sh <variant> <scummvm folder (patched)> <output folder>
# Result: <output>/<variant>/ = build-emscripten of ScummVM (scummvm.js, scummvm.wasm, data/), <output>/<variant>.txt = flags
# and numbers, <output>/mess_<variant>_*.wasm = the same build with function names, with and without Asyncify (only measured).
# Runs in the workflow «FOTAQ» (job «ios»). The variants are described in VARIANTEN.md next to this file.
set -eo pipefail
V="$1"; S="$2"; O="$3"; H="$(cd "$(dirname "$0")" && pwd)"
EMSDK_VERSION="${EMSDK_VERSION:-4.0.10}"
mkdir -p "$O"; cd "$S"
git checkout -q -- configure
case "$V" in
  a) # the data in pieces + small memory; Asyncify and -O2 as in fotaq-1 (tells whether the memory for the data was the cause)
     python3 -I "$H/ios_konfig.py" configure --opt O2 | tee "$O/$V.txt" ;;
  b) # the same, plus small functions: -Oz and Asyncify kept away from code that can never wait (asyncify_remove.txt)
     python3 -I "$H/ios_konfig.py" configure --opt Oz --extra "-s ASYNCIFY_REMOVE=@$H/asyncify_remove.txt" | tee "$O/$V.txt" ;;
  *) echo "unknown variant $V"; exit 1 ;;
esac
n=$(find . -path ./dists -prune -o \( -name '*.o' -o -name '*.a' \) -type f -print | wc -l)
find . -path ./dists -prune -o \( -name '*.o' -o -name '*.a' \) -type f -exec rm -f {} +
rm -rf build-emscripten scummvm.html scummvm.js scummvm.wasm
echo "variant $V: $n old object files removed"
./dists/emscripten/build.sh build --disable-all-engines --enable-engine=queen --enable-release \
  --enable-vorbis --enable-ogg --enable-mad --enable-zlib --enable-png --datadir=/data \
  --disable-detection-full --disable-cloud --disable-tts --disable-mt32emu --disable-lua --disable-tinygl --disable-bink \
  --disable-fluidsynth --disable-eventrecorder --disable-enet --disable-sdlnet --disable-libcurl --disable-discord \
  --disable-freetype2 --disable-jpeg --disable-gif --disable-hq-scalers --disable-edge-scalers > "$O/bau_$V.log" 2>&1 \
  || { tail -60 "$O/bau_$V.log"; echo "::error::variant $V: build failed"; exit 1; }
grep -v '^\(emcc\|em++\|  C\|    C\)' "$O/bau_$V.log" | tail -25
test -s build-emscripten/scummvm.wasm || { echo "::error::variant $V: no scummvm.wasm"; exit 1; }
grep -q "define USE_VORBIS" config.h && grep -q "define USE_MAD" config.h || { echo "::error::Vorbis or MAD missing"; exit 1; }
{ echo "LDFLAGS:"; grep -E '^LDFLAGS' config.mk; echo "CXXFLAGS:"; grep -E '^CXXFLAGS' config.mk | head -12; } >> "$O/$V.txt"
rm -rf "$O/$V"; cp -r build-emscripten "$O/$V"

# ---- measuring: the same objects linked again with function names, once with and once without Asyncify -------------------
set +e
source "dists/emscripten/emsdk-$EMSDK_VERSION/emsdk_env.sh" > /dev/null 2>&1
set -e
link() {
  cp config.mk config.mk.keep; printf '\nLDFLAGS += %s\n' "$2" >> config.mk
  rm -f scummvm.html scummvm.js scummvm.wasm
  local t0=$SECONDS ok=0
  emmake make scummvm.html > "$O/link_${V}_$1.log" 2>&1 && ok=1
  mv config.mk.keep config.mk
  if [ $ok = 1 ] && [ -s scummvm.wasm ]; then cp scummvm.wasm "$O/mess_${V}_$1.wasm"; echo "link $1: $((SECONDS - t0)) s"; else echo "link $1 failed:"; tail -15 "$O/link_${V}_$1.log"; fi
}
link namen "--profiling-funcs"
link ohne "--profiling-funcs -s ASYNCIFY=0"
{
  echo "== variant $V: the build as it is delivered (no names)"
  python3 -I "$H/wasm_funktionen.py" "$O/$V/scummvm.wasm" --top 12
  echo "KENNZAHLEN $V $(python3 -I "$H/wasm_funktionen.py" "$O/$V/scummvm.wasm" --json)"
  if [ -s "$O/mess_${V}_namen.wasm" ]; then
    echo "== variant $V: with names (and the size without Asyncify)"
    if [ -s "$O/mess_${V}_ohne.wasm" ]; then python3 -I "$H/wasm_funktionen.py" "$O/mess_${V}_namen.wasm" --ohne "$O/mess_${V}_ohne.wasm" --top "${TOP:-70}"
    else python3 -I "$H/wasm_funktionen.py" "$O/mess_${V}_namen.wasm" --top "${TOP:-70}"; fi
  fi
} | tee -a "$O/$V.txt"
ls -la "$O/$V"
