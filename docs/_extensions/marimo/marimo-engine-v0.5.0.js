// deno:https://jsr.io/@std/internal/1.0.14/_os.ts
function checkWindows() {
  const global = globalThis;
  const platform = global.process?.platform;
  if (typeof platform === "string") return platform.startsWith("win");
  const os = global.Deno?.build?.os;
  if (typeof os === "string") return os === "windows";
  return global.navigator?.platform?.startsWith("Win") ?? false;
}

// deno:https://jsr.io/@std/internal/1.0.14/os.ts
var isWindows = checkWindows();

// deno:https://jsr.io/@std/path/1.1.6/_common/assert_path.ts
function assertPath(path) {
  if (typeof path !== "string") {
    throw new TypeError(`Path must be a string, received "${JSON.stringify(path)}"`);
  }
}

// deno:https://jsr.io/@std/path/1.1.6/_common/from_file_url.ts
function assertArg(url) {
  url = url instanceof URL ? url : new URL(url);
  if (url.protocol !== "file:") {
    throw new TypeError(`URL must be a file URL: received "${url.protocol}"`);
  }
  return url;
}

// deno:https://jsr.io/@std/path/1.1.6/posix/from_file_url.ts
function fromFileUrl(url) {
  url = assertArg(url);
  return decodeURIComponent(url.pathname.replace(/%(?![0-9A-Fa-f]{2})/g, "%25"));
}

// deno:https://jsr.io/@std/path/1.1.6/_common/strip_trailing_separators.ts
function stripTrailingSeparators(segment, isSep) {
  if (segment.length <= 1) {
    return segment;
  }
  let end = segment.length;
  for (let i = segment.length - 1; i > 0; i--) {
    if (isSep(segment.charCodeAt(i))) {
      end = i;
    } else {
      break;
    }
  }
  return segment.slice(0, end);
}

// deno:https://jsr.io/@std/path/1.1.6/_common/constants.ts
var CHAR_UPPERCASE_A = 65;
var CHAR_LOWERCASE_A = 97;
var CHAR_UPPERCASE_Z = 90;
var CHAR_LOWERCASE_Z = 122;
var CHAR_DOT = 46;
var CHAR_FORWARD_SLASH = 47;
var CHAR_BACKWARD_SLASH = 92;
var CHAR_COLON = 58;

// deno:https://jsr.io/@std/path/1.1.6/posix/_util.ts
function isPosixPathSeparator(code) {
  return code === CHAR_FORWARD_SLASH;
}

// deno:https://jsr.io/@std/path/1.1.6/windows/_util.ts
function isPosixPathSeparator2(code) {
  return code === CHAR_FORWARD_SLASH;
}
function isPathSeparator(code) {
  return code === CHAR_FORWARD_SLASH || code === CHAR_BACKWARD_SLASH;
}
function isWindowsDeviceRoot(code) {
  return code >= CHAR_LOWERCASE_A && code <= CHAR_LOWERCASE_Z || code >= CHAR_UPPERCASE_A && code <= CHAR_UPPERCASE_Z;
}

// deno:https://jsr.io/@std/path/1.1.6/windows/from_file_url.ts
function fromFileUrl2(url) {
  url = assertArg(url);
  let path = decodeURIComponent(url.pathname.replace(/\//g, "\\").replace(/%(?![0-9A-Fa-f]{2})/g, "%25")).replace(/^\\*([A-Za-z]:)(\\|$)/, "$1\\");
  if (url.hostname !== "") {
    path = `\\\\${url.hostname}${path}`;
  }
  return path;
}

// deno:https://jsr.io/@std/path/1.1.6/_common/dirname.ts
function assertArg2(path) {
  assertPath(path);
  if (path.length === 0) return ".";
}

// deno:https://jsr.io/@std/path/1.1.6/posix/dirname.ts
function dirname(path) {
  if (path instanceof URL) {
    path = fromFileUrl(path);
  }
  assertArg2(path);
  let end = -1;
  let matchedNonSeparator = false;
  for (let i = path.length - 1; i >= 1; --i) {
    if (isPosixPathSeparator(path.charCodeAt(i))) {
      if (matchedNonSeparator) {
        end = i;
        break;
      }
    } else {
      matchedNonSeparator = true;
    }
  }
  if (end === -1) {
    return isPosixPathSeparator(path.charCodeAt(0)) ? "/" : ".";
  }
  return stripTrailingSeparators(path.slice(0, end), isPosixPathSeparator);
}

// deno:https://jsr.io/@std/path/1.1.6/windows/dirname.ts
function dirname2(path) {
  if (path instanceof URL) {
    path = fromFileUrl2(path);
  }
  assertArg2(path);
  const len = path.length;
  let rootEnd = -1;
  let end = -1;
  let matchedSlash = true;
  let offset = 0;
  const code = path.charCodeAt(0);
  if (len > 1) {
    if (isPathSeparator(code)) {
      rootEnd = offset = 1;
      if (isPathSeparator(path.charCodeAt(1))) {
        let j = 2;
        let last = j;
        for (; j < len; ++j) {
          if (isPathSeparator(path.charCodeAt(j))) break;
        }
        if (j < len && j !== last) {
          last = j;
          for (; j < len; ++j) {
            if (!isPathSeparator(path.charCodeAt(j))) break;
          }
          if (j < len && j !== last) {
            last = j;
            for (; j < len; ++j) {
              if (isPathSeparator(path.charCodeAt(j))) break;
            }
            if (j === len) {
              return path;
            }
            if (j !== last) {
              rootEnd = offset = j + 1;
            }
          }
        }
      }
    } else if (isWindowsDeviceRoot(code)) {
      if (path.charCodeAt(1) === CHAR_COLON) {
        rootEnd = offset = 2;
        if (len > 2) {
          if (isPathSeparator(path.charCodeAt(2))) rootEnd = offset = 3;
        }
      }
    }
  } else if (isPathSeparator(code)) {
    return path;
  }
  for (let i = len - 1; i >= offset; --i) {
    if (isPathSeparator(path.charCodeAt(i))) {
      if (!matchedSlash) {
        end = i;
        break;
      }
    } else {
      matchedSlash = false;
    }
  }
  if (end === -1) {
    if (rootEnd === -1) return ".";
    else end = rootEnd;
  }
  return stripTrailingSeparators(path.slice(0, end), isPosixPathSeparator2);
}

// deno:https://jsr.io/@std/path/1.1.6/dirname.ts
function dirname3(path) {
  return isWindows ? dirname2(path) : dirname(path);
}

// deno:https://jsr.io/@std/path/1.1.6/from_file_url.ts
function fromFileUrl3(url) {
  return isWindows ? fromFileUrl2(url) : fromFileUrl(url);
}

// deno:https://jsr.io/@std/path/1.1.6/_common/normalize.ts
function assertArg4(path) {
  assertPath(path);
  if (path.length === 0) return ".";
}

// deno:https://jsr.io/@std/path/1.1.6/_common/normalize_string.ts
function normalizeString(path, allowAboveRoot, separator, isPathSeparator2) {
  let res = "";
  let lastSegmentLength = 0;
  let lastSlash = -1;
  let dots = 0;
  let code;
  for (let i = 0; i <= path.length; ++i) {
    if (i < path.length) code = path.charCodeAt(i);
    else if (isPathSeparator2(code)) break;
    else code = CHAR_FORWARD_SLASH;
    if (isPathSeparator2(code)) {
      if (lastSlash === i - 1 || dots === 1) {
      } else if (lastSlash !== i - 1 && dots === 2) {
        if (res.length < 2 || lastSegmentLength !== 2 || res.charCodeAt(res.length - 1) !== CHAR_DOT || res.charCodeAt(res.length - 2) !== CHAR_DOT) {
          if (res.length > 2) {
            const lastSlashIndex = res.lastIndexOf(separator);
            if (lastSlashIndex === -1) {
              res = "";
              lastSegmentLength = 0;
            } else {
              res = res.slice(0, lastSlashIndex);
              lastSegmentLength = res.length - 1 - res.lastIndexOf(separator);
            }
            lastSlash = i;
            dots = 0;
            continue;
          } else if (res.length === 2 || res.length === 1) {
            res = "";
            lastSegmentLength = 0;
            lastSlash = i;
            dots = 0;
            continue;
          }
        }
        if (allowAboveRoot) {
          if (res.length > 0) res += `${separator}..`;
          else res = "..";
          lastSegmentLength = 2;
        }
      } else {
        if (res.length > 0) res += separator + path.slice(lastSlash + 1, i);
        else res = path.slice(lastSlash + 1, i);
        lastSegmentLength = i - lastSlash - 1;
      }
      lastSlash = i;
      dots = 0;
    } else if (code === CHAR_DOT && dots !== -1) {
      ++dots;
    } else {
      dots = -1;
    }
  }
  return res;
}

// deno:https://jsr.io/@std/path/1.1.6/posix/normalize.ts
function normalize(path) {
  if (path instanceof URL) {
    path = fromFileUrl(path);
  }
  assertArg4(path);
  const isAbsolute3 = isPosixPathSeparator(path.charCodeAt(0));
  const trailingSeparator = isPosixPathSeparator(path.charCodeAt(path.length - 1));
  path = normalizeString(path, !isAbsolute3, "/", isPosixPathSeparator);
  if (path.length === 0 && !isAbsolute3) path = ".";
  if (path.length > 0 && trailingSeparator) path += "/";
  if (isAbsolute3) return `/${path}`;
  return path;
}

// deno:https://jsr.io/@std/path/1.1.6/posix/join.ts
function join(path, ...paths) {
  if (path === void 0) return ".";
  if (path instanceof URL) {
    path = fromFileUrl(path);
  }
  paths = path ? [
    path,
    ...paths
  ] : paths;
  paths.forEach((path2) => assertPath(path2));
  const joined = paths.filter((path2) => path2.length > 0).join("/");
  return joined === "" ? "." : normalize(joined);
}

// deno:https://jsr.io/@std/path/1.1.6/windows/normalize.ts
function normalize2(path) {
  if (path instanceof URL) {
    path = fromFileUrl2(path);
  }
  assertArg4(path);
  const len = path.length;
  let rootEnd = 0;
  let device;
  let isAbsolute3 = false;
  const code = path.charCodeAt(0);
  if (len > 1) {
    if (isPathSeparator(code)) {
      isAbsolute3 = true;
      if (isPathSeparator(path.charCodeAt(1))) {
        let j = 2;
        let last = j;
        for (; j < len; ++j) {
          if (isPathSeparator(path.charCodeAt(j))) break;
        }
        if (j < len && j !== last) {
          const firstPart = path.slice(last, j);
          last = j;
          for (; j < len; ++j) {
            if (!isPathSeparator(path.charCodeAt(j))) break;
          }
          if (j < len && j !== last) {
            last = j;
            for (; j < len; ++j) {
              if (isPathSeparator(path.charCodeAt(j))) break;
            }
            if (j === len) {
              return `\\\\${firstPart}\\${path.slice(last)}\\`;
            } else if (j !== last) {
              device = `\\\\${firstPart}\\${path.slice(last, j)}`;
              rootEnd = j;
            }
          }
        }
      } else {
        rootEnd = 1;
      }
    } else if (isWindowsDeviceRoot(code)) {
      if (path.charCodeAt(1) === CHAR_COLON) {
        device = path.slice(0, 2);
        rootEnd = 2;
        if (len > 2) {
          if (isPathSeparator(path.charCodeAt(2))) {
            isAbsolute3 = true;
            rootEnd = 3;
          }
        }
      }
    }
  } else if (isPathSeparator(code)) {
    return "\\";
  }
  let tail;
  if (rootEnd < len) {
    tail = normalizeString(path.slice(rootEnd), !isAbsolute3, "\\", isPathSeparator);
  } else {
    tail = "";
  }
  if (tail.length === 0 && !isAbsolute3) tail = ".";
  if (tail.length > 0 && isPathSeparator(path.charCodeAt(len - 1))) {
    tail += "\\";
  }
  if (device === void 0) {
    if (isAbsolute3) {
      if (tail.length > 0) return `\\${tail}`;
      else return "\\";
    }
    return tail;
  } else if (isAbsolute3) {
    if (tail.length > 0) return `${device}\\${tail}`;
    else return `${device}\\`;
  }
  return device + tail;
}

// deno:https://jsr.io/@std/path/1.1.6/windows/join.ts
function join2(path, ...paths) {
  if (path instanceof URL) {
    path = fromFileUrl2(path);
  }
  paths = path ? [
    path,
    ...paths
  ] : paths;
  paths.forEach((path2) => assertPath(path2));
  paths = paths.filter((path2) => path2.length > 0);
  if (paths.length === 0) return ".";
  let needsReplace = true;
  let slashCount = 0;
  const firstPart = paths[0];
  if (isPathSeparator(firstPart.charCodeAt(0))) {
    ++slashCount;
    const firstLen = firstPart.length;
    if (firstLen > 1) {
      if (isPathSeparator(firstPart.charCodeAt(1))) {
        ++slashCount;
        if (firstLen > 2) {
          if (isPathSeparator(firstPart.charCodeAt(2))) ++slashCount;
          else {
            needsReplace = false;
          }
        }
      }
    }
  }
  let joined = paths.join("\\");
  if (needsReplace) {
    for (; slashCount < joined.length; ++slashCount) {
      if (!isPathSeparator(joined.charCodeAt(slashCount))) break;
    }
    if (slashCount >= 2) joined = `\\${joined.slice(slashCount)}`;
  }
  return normalize2(joined);
}

// deno:https://jsr.io/@std/path/1.1.6/join.ts
function join3(path, ...paths) {
  return isWindows ? join2(path, ...paths) : join(path, ...paths);
}

// src/engine/authoring.ts
var MARIMO_CELL_REGEX = /^\s{0,3}(`{3,})\s*(?=(?:\{)?\.?((?:python|sql|markdown)(?:\.marimo)?|marimo)(?=[\s}]))(?:(?:python|sql|markdown)\s+\{(?=(?:\.marimo(?=[\s}])|[^}]*\s\.marimo(?=[\s}])))[^}]*\}|\{(?:(?:python|sql|markdown)\.marimo(?=[\s}])|(?:python|sql|markdown)(?=\s)(?=[^}]*\s\.marimo(?=[\s}]))|\.?marimo(?=[\s}]))[^}]*\})\s*$/;
var MARKDOWN_FENCE_REGEX = /^\s{0,3}(`{3,}|~{3,})/;
var MARKDOWN_FENCE_CLOSE_REGEX = /^\s{0,3}(`{3,}|~{3,})\s*$/;
function containsMarimoFence(markdown) {
  let enclosingFence;
  for (const line of markdown.split(/\r?\n/)) {
    if (enclosingFence) {
      const closingFence = line.match(MARKDOWN_FENCE_CLOSE_REGEX)?.[1];
      if (closingFence?.[0] === enclosingFence[0] && closingFence.length >= enclosingFence.length) {
        enclosingFence = void 0;
      }
      continue;
    }
    if (MARIMO_CELL_REGEX.test(line)) return true;
    enclosingFence = line.match(MARKDOWN_FENCE_REGEX)?.[1];
  }
  return false;
}
function isMarimoCell(cell) {
  if (typeof cell.cell_type !== "object" || !("language" in cell.cell_type)) {
    return false;
  }
  const language = cell.cell_type.language;
  if (language !== "python" && language !== "sql" && language !== "markdown" && language !== "marimo" && language !== "python.marimo" && language !== "sql.marimo" && language !== "markdown.marimo") {
    return false;
  }
  const firstLine = cell.sourceVerbatim.value.split("\n", 1)[0] ?? "";
  return MARIMO_CELL_REGEX.test(firstLine);
}

// src/engine/browser-assets.ts
var EXTENSION_CONFIG = "_extension.yml";
function writeBrowserHeader(extensionDir, tempDir) {
  const version = extensionVersion(extensionDir);
  const assetsDir = join3(extensionDir, "assets");
  const browser = Deno.readTextFileSync(join3(assetsDir, `browser-v${version}.js`)).replace(/<\/script/gi, "<\\/script");
  const styles = Deno.readTextFileSync(join3(assetsDir, `islands-bridge-v${version}.css`)).replace(/<\/style/gi, "<\\/style");
  const header = [
    `<style data-marimo-islands>${styles}</style>`,
    `<script type="module" data-marimo-islands>${browser}<\/script>`
  ].join("\n");
  const path = Deno.makeTempFileSync({
    dir: tempDir,
    prefix: "marimo-header-",
    suffix: ".html"
  });
  Deno.writeTextFileSync(path, header);
  return path;
}
function extensionVersion(extensionDir) {
  const config = Deno.readTextFileSync(join3(extensionDir, EXTENSION_CONFIG));
  const match = config.match(/^version:\s*["']?([^"'\s#]+)["']?\s*$/m);
  if (!match) throw new Error("marimo extension version is missing");
  return match[1];
}

// ../../../../.cache/deno/npm/registry.npmjs.org/@marimo-team/mdx-marimo/0.0.5/dist/bridge/protocol/index.js
function pageCellPayload(page, cell) {
  return {
    protocolVersion: page.protocolVersion,
    app: page.app,
    cell: pageCell(cell)
  };
}
function pageCellReferencePayload(page, cell) {
  if (!page.app) return pageCellPayload(page, cell);
  return {
    protocolVersion: page.protocolVersion,
    appId: page.app.id,
    cell: pageCell(cell)
  };
}
function projectPageCellPayloads(page) {
  const indices = page.cells.map((cell) => cell.index);
  if (indices.some((index, position) => index !== position)) {
    const expected = page.cells.map((_, index) => index);
    throw new Error(`marimo compiler returned cell indices [${indices.join(", ")}]; expected [${expected.join(", ")}]`);
  }
  const carrierIndex = page.app ? page.cells.find((cell) => cell.options.render.include)?.index : void 0;
  return page.cells.map((cell) => {
    if (!cell.options.render.include) return null;
    return cell.index === carrierIndex ? pageCellPayload(page, cell) : pageCellReferencePayload(page, cell);
  });
}
function encodePageCellPayload(payload) {
  const bytes = new TextEncoder().encode(JSON.stringify(payload));
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, "");
}
function isCompiledMarimoPage(value) {
  return isRecord(value) && value.protocolVersion === 2 && (value.app === null || isPageRuntime(value.app)) && isArrayOf(value.cells, isCompiledCell) && isArrayOf(value.diagnostics, isDiagnostic);
}
function isCompiledCell(value) {
  return isPageCell(value) && "output" in value && isCompiledOutput(value.output);
}
function isPageCell(value) {
  return isRecord(value) && isFiniteNumber(value.index) && typeof value.html === "string" && isCellOptions(value.options) && (value.diagnostics === void 0 || isArrayOf(value.diagnostics, isDiagnostic));
}
function isCompiledOutput(value) {
  return value === null || isRecord(value) && typeof value.mimetype === "string" && isJsonValue(value.data) && typeof value.html === "string";
}
function pageCell(cell) {
  const projected = {
    index: cell.index,
    html: cell.html,
    options: cell.options
  };
  if (cell.diagnostics !== void 0) projected.diagnostics = cell.diagnostics;
  return projected;
}
function isPageRuntime(value) {
  return isRecord(value) && typeof value.id === "string" && value.id.length > 0 && isFiniteNumber(value.runtimeCellCount) && isRuntimeAssets(value.assets) && (value.notebookCode === void 0 || typeof value.notebookCode === "string");
}
function isRuntimeAssets(value) {
  return isRecord(value) && isArrayOf(value.moduleScripts, isString) && isArrayOf(value.links, isStringRecord) && (value.headTags === void 0 || isArrayOf(value.headTags, isHeadTag)) && (value.version === void 0 || typeof value.version === "string");
}
function isHeadTag(value) {
  return isRecord(value) && typeof value.tag === "string" && isStringRecord(value.attrs) && (value.text === void 0 || typeof value.text === "string");
}
function isCellOptions(value) {
  return isRecord(value) && (value.language === "python" || value.language === "sql" || value.language === "markdown") && isRenderOptions(value.render) && isRecord(value.execution) && typeof value.execution.enabled === "boolean" && isRecord(value.marimo) && typeof value.marimo.disabled === "boolean" && typeof value.marimo.unparsable === "boolean" && (value.sql === void 0 || isRecord(value.sql) && (value.sql.outputName === void 0 || typeof value.sql.outputName === "string") && (value.sql.engine === void 0 || typeof value.sql.engine === "string")) && (value.name === void 0 || typeof value.name === "string") && (value.column === void 0 || isFiniteNumber(value.column));
}
function isRenderOptions(value) {
  return isRecord(value) && typeof value.source === "boolean" && typeof value.output === "boolean" && typeof value.include === "boolean" && typeof value.editor === "boolean" && typeof value.error === "boolean" && typeof value.serverOutput === "boolean";
}
function isDiagnostic(value) {
  return isRecord(value) && (value.severity === "warning" || value.severity === "error") && typeof value.message === "string" && (value.cellIndex === void 0 || isFiniteNumber(value.cellIndex)) && (value.line === void 0 || isFiniteNumber(value.line));
}
function isJsonValue(value) {
  if (value === null || typeof value === "string" || typeof value === "boolean") return true;
  if (isFiniteNumber(value)) return true;
  if (Array.isArray(value)) return Array.from(value).every(isJsonValue);
  return isRecord(value) && Object.values(value).every(isJsonValue);
}
function isStringRecord(value) {
  return isRecord(value) && Object.values(value).every(isString);
}
function isArrayOf(value, guard) {
  return Array.isArray(value) && Array.from(value).every(guard);
}
function isString(value) {
  return typeof value === "string";
}
function isFiniteNumber(value) {
  return typeof value === "number" && Number.isFinite(value);
}
function isRecord(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

// src/island-element.ts
var MARIMO_ELEMENT_NAME = "marimo-quarto-island";

// src/engine/projection.ts
function projectInteractivePage(page) {
  const cells = page.cells;
  const sources = cells.map((cell) => cell.authorSource);
  const payloadPage = {
    ...page,
    cells: cells.map(({ authorSource: _authorSource, ...cell }) => cell)
  };
  return projectPageCellPayloads(payloadPage).map((payload, index) => {
    const source = sources[index];
    const code = source ? authorSourceBlock(source) : "";
    return code + (payload ? rawHtml(renderIsland(payload)) : "");
  });
}
function authorSourceBlock(source) {
  const attributes = [
    `.${source.language}`,
    ".cell-code"
  ];
  if (source.fold) {
    attributes.push(`code-fold="${source.fold === "show" ? "show" : "true"}"`);
  }
  if (source.summary) {
    attributes.push(`code-summary="${escapeAttribute(source.summary)}"`);
  }
  return fencedCode(source.code, `{${attributes.join(" ")}}`);
}
function escapeAttribute(value) {
  return value.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
}
async function projectStaticPage(outputs, htmlToMarkdown2, preserveHtml = false) {
  return await Promise.all(outputs.map((output) => renderStaticOutput(output, htmlToMarkdown2, preserveHtml)));
}
function validateProjectionCount(projected, actualCellCount) {
  if (projected.length !== actualCellCount) {
    throw new Error(`marimo compiler returned ${projected.length} cells for ${actualCellCount} source blocks`);
  }
}
function renderIsland(payload) {
  return [
    `<${MARIMO_ELEMENT_NAME}`,
    ` data-marimo-payload="${encodePageCellPayload(payload)}"`,
    ' data-marimo-payload-encoding="base64url"',
    ' data-marimo-theme-mode="auto"',
    `></${MARIMO_ELEMENT_NAME}>`
  ].join("");
}
async function renderStaticOutput(output, htmlToMarkdown2, preserveHtml) {
  let result = "";
  if (output.displayCode && output.code) {
    result += authorSourceBlock({
      code: output.code,
      language: output.language,
      fold: output.fold,
      summary: output.summary
    });
  }
  if (!output.value) return result;
  switch (output.type) {
    case "figure":
      return `${result}![Generated Figure](<${output.value}>)

`;
    case "para":
      return `${result}${output.value}

`;
    case "plain":
      return `${result}${fencedCode(output.value)}`;
    case "blockquote":
      return `${result}> ${output.value.replace(/\r?\n/g, "\n> ")}

`;
    case "html":
      if (preserveHtml || /<table[\s>]/i.test(output.value)) {
        return `${result}${rawHtml(output.value)}`;
      }
      return `${result}${await htmlToMarkdown2(output.value)}

`;
  }
}
function fencedCode(value, language = "") {
  const longestRun = Math.max(0, ...Array.from(value.matchAll(/`+/g), (match) => match[0].length));
  const fence = "`".repeat(Math.max(3, longestRun + 1));
  return `${fence}${language}
${value}
${fence}

`;
}
function rawHtml(value) {
  return fencedCode(value, "{=html}");
}

// src/engine/process.ts
var defaultCompilerTimeoutMs = 3e5;
var pythonUtf8Environment = {
  PYTHONUTF8: "1",
  PYTHONIOENCODING: "utf-8"
};
async function runMarimoCompiler(quarto2, options) {
  const extensionDir = dirname3(fromFileUrl3(options.moduleUrl));
  const extractPath = join3(extensionDir, "python", "extract.py");
  let command;
  let args;
  let temporaryDirectory;
  if (options.externalEnv) {
    command = Deno.env.get("QUARTO_PYTHON") || "python";
    args = [
      extractPath
    ];
  } else {
    command = "uv";
    const uvCommand = await constructUvCommand(quarto2, extensionDir, options.pyproject);
    temporaryDirectory = uvCommand.temporaryDirectory;
    args = [
      ...uvCommand.args,
      extractPath
    ];
  }
  args.push(options.input, outputMode(options), options.globalEval ? "yes" : "no");
  let output;
  try {
    output = await executeProcess(quarto2, command, args, options.source);
  } finally {
    if (temporaryDirectory) {
      await removeTemporaryDirectory(temporaryDirectory);
    }
  }
  const value = JSON.parse(output);
  if (isPageExecution(value) || isStaticExecution(value)) return value;
  throw new TypeError("marimo compiler returned an invalid execution payload");
}
function outputMode(options) {
  if (options.interactive) return "html";
  return options.htmlCompatible ? "html-static" : "static";
}
async function constructUvCommand(quarto2, extensionDir, pyproject) {
  const commandPath = join3(extensionDir, "python", "command.py");
  const temporaryDirectory = await Deno.makeTempDir({
    prefix: "quarto-marimo-"
  });
  try {
    const output = await executeProcess(quarto2, "uv", [
      "run",
      "--with",
      "marimo",
      commandPath
    ], pyproject, compilerTimeoutMs(), {
      TEMP: temporaryDirectory,
      TMP: temporaryDirectory,
      TMPDIR: temporaryDirectory
    });
    const value = JSON.parse(output);
    if (!Array.isArray(value) || !value.every((entry) => typeof entry === "string")) {
      throw new TypeError("marimo dependency resolver returned invalid uv arguments");
    }
    return {
      args: value,
      temporaryDirectory
    };
  } catch (error) {
    await removeTemporaryDirectory(temporaryDirectory);
    throw error;
  }
}
async function executeProcess(quarto2, command, args, stdin, timeoutMs = compilerTimeoutMs(), env) {
  const child = new Deno.Command(command, {
    args,
    env: {
      ...pythonUtf8Environment,
      ...env
    },
    stdin: "piped",
    stdout: "piped",
    stderr: "piped"
  }).spawn();
  const outputPromise = child.output();
  const writer = child.stdin.getWriter();
  let timedOut = false;
  const timeout = setTimeout(() => {
    timedOut = true;
    try {
      child.kill("SIGTERM");
    } catch {
    }
  }, timeoutMs);
  let output;
  try {
    await writer.write(new TextEncoder().encode(stdin));
    await writer.close();
    output = await outputPromise;
  } catch (error) {
    if (!timedOut) throw error;
    await outputPromise.catch(() => void 0);
    throw timeoutError(command, args, timeoutMs);
  } finally {
    clearTimeout(timeout);
  }
  if (timedOut) throw timeoutError(command, args, timeoutMs);
  const stderr = new TextDecoder().decode(output.stderr);
  if (stderr) quarto2.console.info(stderr.trim());
  if (!output.success) {
    throw new Error(stderr.trim() || `${command} exited with code ${output.code}`);
  }
  return new TextDecoder().decode(output.stdout);
}
function compilerTimeoutMs() {
  const seconds = Number(Deno.env.get("QUARTO_MARIMO_TIMEOUT_SECONDS") ?? "");
  return Number.isFinite(seconds) && seconds > 0 ? seconds * 1e3 : defaultCompilerTimeoutMs;
}
function timeoutError(command, args, timeoutMs) {
  return new Error(`marimo compilation timed out after ${timeoutMs / 1e3}s while running ${[
    command,
    ...args
  ].join(" ")}`);
}
async function removeTemporaryDirectory(path) {
  await Deno.remove(path, {
    recursive: true
  }).catch(() => void 0);
}
function isPageExecution(value) {
  return isRecord2(value) && value.kind === "page" && isCompiledMarimoPage(value.page);
}
function isStaticExecution(value) {
  return isRecord2(value) && value.kind === "static" && Array.isArray(value.outputs) && value.outputs.every(isStaticOutput);
}
function isStaticOutput(value) {
  return isRecord2(value) && (value.type === "html" || value.type === "figure" || value.type === "para" || value.type === "plain" || value.type === "blockquote") && typeof value.value === "string" && typeof value.displayCode === "boolean" && typeof value.code === "string" && typeof value.language === "string" && (typeof value.fold === "boolean" || value.fold === "show") && (value.summary === null || typeof value.summary === "string");
}
function isRecord2(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

// src/engine/index.ts
var quarto;
var marimoEngineDiscovery = {
  init: (quartoAPI) => {
    quarto = quartoAPI;
  },
  name: "marimo",
  defaultExt: ".qmd",
  defaultYaml: () => [
    "format: html",
    "engine: marimo"
  ],
  defaultContent: () => [
    "```{python .marimo}",
    "import marimo as mo",
    "slider = mo.ui.slider(1, 10, 1)",
    "slider",
    "```"
  ],
  validExtensions: () => [
    ".qmd",
    ".md"
  ],
  claimsFile: (file, extension) => {
    if (![
      ".qmd",
      ".md"
    ].includes(extension.toLowerCase())) return false;
    try {
      return containsMarimoFence(Deno.readTextFileSync(file));
    } catch {
      return false;
    }
  },
  claimsLanguage: (language, firstClass) => {
    if ((language === "python" || language === "sql" || language === "markdown") && firstClass === "marimo") {
      return 2;
    }
    if (language === "python.marimo" || language === "sql.marimo" || language === "markdown.marimo" || language === "marimo") {
      return 1;
    }
    return false;
  },
  canFreeze: true,
  generatesFigures: true,
  checkInstallation: async (configuration) => {
    const report = {};
    if (configuration.jsonResult) {
      const render = configuration.jsonResult.render ??= {};
      render.marimo = report;
    }
    const checkRender = async () => {
      const result = await quarto.system.checkRender({
        content: "```{python .marimo}\n1 + 1\n```\n",
        language: "python",
        services: configuration.services
      });
      if (result.error) {
        if (configuration.jsonResult) {
          report.error = result.error.message;
          return;
        }
        throw result.error;
      }
      report.ok = true;
    };
    if (configuration.jsonResult) {
      await checkRender();
    } else {
      const message = "Checking marimo engine render...";
      await quarto.console.withSpinner({
        message,
        doneMessage: `${message}OK
`
      }, checkRender);
    }
  },
  launch: (_context) => ({
    name: marimoEngineDiscovery.name,
    canFreeze: marimoEngineDiscovery.canFreeze,
    markdownForFile(file) {
      return Promise.resolve(quarto.mappedString.fromFile(file));
    },
    target: (file, _quiet, markdown) => {
      const source = markdown ?? quarto.mappedString.fromFile(file);
      return Promise.resolve({
        source: file,
        input: file,
        markdown: source,
        metadata: quarto.markdownRegex.extractYaml(source.value)
      });
    },
    partitionedMarkdown: (file) => Promise.resolve(quarto.markdownRegex.partition(Deno.readTextFileSync(file))),
    execute: async (options) => {
      const htmlCompatible = quarto.format.isHtmlCompatible(options.format);
      const interactive = isInteractiveFormat(htmlCompatible, options.format.metadata);
      const execution = await quarto.console.withSpinner({
        message: "Executing marimo cells..."
      }, async () => await runMarimoCompiler(quarto, {
        moduleUrl: import.meta.url,
        source: options.target.markdown.value,
        input: options.target.input,
        interactive,
        htmlCompatible,
        ...engineSettings(options.format)
      }));
      const chunks = await quarto.markdownRegex.breakQuartoMd(options.target.markdown, false, false, MARIMO_CELL_REGEX);
      const marimoCells = chunks.cells.filter(isMarimoCell);
      const projected = execution.kind === "page" ? projectInteractivePage(execution.page) : await projectStaticPage(execution.outputs, htmlToMarkdown, htmlCompatible);
      validateProjectionCount(projected, marimoCells.length);
      let index = 0;
      const markdown = chunks.cells.map((cell) => isMarimoCell(cell) ? projected[index++] ?? "" : cell.sourceVerbatim.value).join("");
      return {
        engine: "marimo",
        markdown,
        supporting: [],
        filters: [],
        engineDependencies: execution.kind === "page" ? {
          marimo: [
            BROWSER_RUNTIME
          ]
        } : void 0
      };
    },
    dependencies: (options) => {
      const includes = {};
      if (needsBrowserRuntime(options.dependencies)) {
        const extensionDir = dirname3(fromFileUrl3(import.meta.url));
        includes["include-in-header"] = [
          writeBrowserHeader(extensionDir, options.tempDir)
        ];
      }
      return Promise.resolve({
        includes
      });
    },
    postprocess: (_options) => Promise.resolve()
  })
};
function engineSettings(format3) {
  return {
    globalEval: format3.execute.eval !== false,
    externalEnv: format3.metadata["external-env"] === true,
    pyproject: String(format3.metadata.pyproject ?? "")
  };
}
function isInteractiveFormat(isHtmlCompatible, metadata) {
  return isHtmlCompatible && metadata.interactive !== false;
}
var BROWSER_RUNTIME = "browser-runtime";
function needsBrowserRuntime(dependencies) {
  return (dependencies ?? []).includes(BROWSER_RUNTIME);
}
async function htmlToMarkdown(html) {
  const result = await quarto.system.pandoc([
    "-f",
    "html",
    "-t",
    "markdown"
  ], html);
  if (!result.success) {
    throw new Error(result.stderr || "Pandoc could not convert marimo HTML");
  }
  return result.stdout || "";
}
var engine_default = marimoEngineDiscovery;
export {
  BROWSER_RUNTIME,
  engine_default as default,
  engineSettings,
  isInteractiveFormat,
  needsBrowserRuntime
};
