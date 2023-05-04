declare module "js-vue-logger" {
  export const DEBUG = "DEBUG";
  export function debug(...args: Any[]);
  export function info(...args: Any[]);
  export function warn(...args: Any[]);
  export function error(...args: Any[]);
  export function trace(...args: Any[]);
  export function useDefaults();
  export function setLevel(level: string);
}
