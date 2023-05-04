import {
  Camera,
  Raycaster,
  Vector2,
  Vector3,
  OrthographicCamera,
  Scene,
} from "three";

import type { Object3D } from "three";
import type { ZoomPanControls } from "@/plugins/threejs/threex/controls/useZoomPanControls";
import HoverEventHandler from "./HoverEventHandler";
import type { PcbEditorStore, ProbingPlanePosition } from "@/stores/pcbEditor";
import { useSelectionService } from "./useSelectionService";

const raycaster = new Raycaster();

export interface EditorMouseEventMap {
  event: MouseEvent;
  objectsUnderCursor: Array<Object3D>;
}

export interface EditorTouchEventMap {
  event: TouchEvent;
  objectsUnderCursor: Array<Object3D>;
}

export interface Handler {
  activate(): void;
  deactivate(): void;
}

const ENTER = "Enter";
const ESCAPE = "Escape";

export default class PcbEventDispatcher {
  private camera: Camera;
  private scene: Scene;
  private overlay: HTMLElement;
  private store;
  private hoverEventHandler: HoverEventHandler;
  private zoomPanControls: ZoomPanControls;

  constructor(
    camera: OrthographicCamera,
    scene: Scene,
    zoomPanControls: ZoomPanControls,
    overlay: HTMLElement,
    store: PcbEditorStore
  ) {
    this.camera = camera;
    this.scene = scene;
    this.zoomPanControls = zoomPanControls;
    this.overlay = overlay;
    this.store = store;

    this.hoverEventHandler = new HoverEventHandler();
  }

  dispatchTouchEvent(type: string, event: TouchEvent) {
    //logger.debug("dispatchTouchEvent: ", type);
    // Calculate the first touch position
    const touchPos = this.calculateFirstTouchPosition(event);
    if (touchPos) {
      const { touchX, touchY } = touchPos;
      this.store.currentProbingPlanePosition =
        this.getProbingAreaPositionOfCursor(touchX, touchY);

      // Mode handling
      if (this.store.currentMode) {
        this.store.currentMode.handle(type, event);
      }

      if (!event.defaultPrevented) {
        // Handle event dispatching to the objects under the cursor
        const objectsUnderCursor = this.getObjectsUnderCursor(touchX, touchY);
        const editorTouchEventMap: EditorTouchEventMap = {
          event,
          objectsUnderCursor,
        };
        this.hoverEventHandler.handleTouch(type, editorTouchEventMap);
      }
    }
    switch (type) {
      case "touchmove":
        this.zoomPanControls.onTouchMove(event);
        event.preventDefault();
        break;
      case "touchstart":
        this.zoomPanControls.onTouchStart(event);
        event.preventDefault();
        break;
    }
  }

  /*
   * Global event dispatcher of the interactive PCB editor
   */
  dispatchMouseEvent(type: string, event: MouseEvent | WheelEvent) {
    //logger.debug("dispatchMouseEvent:", type);
    // Calculate the current mouse position
    const mousePos = this.calculateMousePosition(event);
    if (mousePos) {
      const { mouseX, mouseY } = mousePos;
      // Update the probing plane Position
      this.store.currentProbingPlanePosition =
        this.getProbingAreaPositionOfCursor(mouseX, mouseY);

      const objectsUnderCursor = this.getObjectsUnderCursor(mouseX, mouseY);
      const editorMouseEventMap: EditorMouseEventMap = {
        event,
        objectsUnderCursor,
      };

      if (type === "click") {
        // TODO Remove this hack to bring the focus to the overlay
        //      to catch keyboard events!
        this.overlay.focus();
      }

      this.hoverEventHandler.handleMouse(type, editorMouseEventMap);
    }

    if (this.store.currentMode) {
      this.store.currentMode.handle(type, event);
    }

    // Cancel if the component prevents the default handler
    if (event.defaultPrevented) {
      return;
    }

    // 3. priority: Default view controller
    switch (type) {
      case "mousedown":
        this.zoomPanControls.onMouseDown(event as MouseEvent);
        break;
      case "mousewheel":
        this.zoomPanControls.onMouseWheel(event as WheelEvent);
        break;
    }
  }

  dispatchKeyboardEvent(type: string, event: KeyboardEvent) {
    if (event.key === ESCAPE) {
      if (this.store.currentMode) {
        this.store.currentMode.deactivate();
        this.store.currentMode = null;
      } else {
        useSelectionService().cancelSelection();
        this.store.clearSelection();
      }
    }
    if (event.key === ENTER) {
      useSelectionService().commitSelection();
    }
  }

  private calculateMousePosition(event: MouseEvent) {
    if (!event.target) return null;
    const viewportSize = (event.target as HTMLElement).getBoundingClientRect();
    const mouseX =
      ((event.clientX - viewportSize.left) / viewportSize.width) * 2 - 1;
    const mouseY =
      -((event.clientY - viewportSize.top) / viewportSize.height) * 2 + 1;
    return { mouseX, mouseY };
  }

  private calculateFirstTouchPosition(event: TouchEvent) {
    if (!event.target) return null;
    const viewportSize = (event.target as HTMLElement).getBoundingClientRect();
    const touchX =
      ((event.touches[0].clientX - viewportSize.left) / viewportSize.width) *
        2 -
      1;
    const touchY =
      -((event.touches[0].clientY - viewportSize.top) / viewportSize.height) *
        2 +
      1;
    return { touchX, touchY };
  }

  private getObjectsUnderCursor(mouseX: number, mouseY: number) {
    const mouse = new Vector2();
    mouse.x = mouseX;
    mouse.y = mouseY;

    // Update the raycaster
    raycaster.setFromCamera(mouse, this.camera);
    const intersects = raycaster.intersectObjects(this.scene.children, true);

    // Filter only selectable objects
    const objectsUnderCursor = intersects
      .filter(
        (intersection) =>
          intersection.object.userData &&
          intersection.object.userData.isSelectable
      )
      .map((intersection) => intersection.object)
      .sort((objA, objB) => objB.renderOrder - objA.renderOrder);

    return objectsUnderCursor;
  }

  private getProbingAreaPositionOfCursor(
    mouseX: number,
    mouseY: number
  ): ProbingPlanePosition | null {
    const mouse = new Vector2();
    mouse.x = mouseX;
    mouse.y = mouseY;

    // Update the raycaster
    // TODO Performance can be increased by putting the probing plane on a
    // separate layer and intersect only with elements on this layer here!!
    raycaster.setFromCamera(mouse, this.camera);
    const intersects = raycaster.intersectObjects(this.scene.children, true);

    // Check for an intersection with the PROBoter probing area
    const areaIntersection = intersects.find(
      (intersection) =>
        intersection.object.userData &&
        intersection.object.userData.type === "PROBING_AREA"
    );

    // TODO Fix hard-coded probing area values here!!
    const probingAreaWidth = 300;
    const probingAreaHeight = 200;
    if (areaIntersection && areaIntersection.uv) {
      return new Vector3(
        -probingAreaWidth * (areaIntersection.uv.x - 0.5),
        probingAreaHeight * (areaIntersection.uv.y - 0.5),
        0
      );
    } else {
      return null;
    }
  }
}
