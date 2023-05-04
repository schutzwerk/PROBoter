declare module "@/plugins/threejs/threex/controls/useZoomPanControls" {
  import type { OrthographicCamera } from "three";
  // TODO Add full type declaration here!
  export interface ZoomPanControls {
    new (
      camera: OrthographicCamera | undefined,
      domElement: HTMLCanvasElement | undefined
    );
    enableRotate: bool;
    onTouchStart(event: TouchEvent);
    onTouchMove(event: TouchEvent);
    onMouseDown(event: MouseEvent);
    onMouseWheel(event: WheelEvent);
    update();
    reset();
  }

  const module: ZoomPanControls;
  export = module;
}
