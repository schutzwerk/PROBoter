import type { Object3D } from "three";
import type {
  EditorMouseEventMap,
  EditorTouchEventMap,
} from "./usePcbEventDispatcher";

export default class HoverEventHandler {
  private hoveredObject: Object3D | null = null;

  handleTouch(type: string, event: EditorTouchEventMap) {
    // Determine the threeJS objects under the cursor
    const objectsUnderCursor = event.objectsUnderCursor;

    // Event forwarding to the object under the cursor
    for (let i = 0; i < objectsUnderCursor.length; i++) {
      objectsUnderCursor[i].userData.vueObject.$emit(type, event.event);
      if (event.event.defaultPrevented) return;
    }
  }

  handleMouse(type: string, event: EditorMouseEventMap) {
    // Determine the threeJS objects under the cursor
    const objectsUnderCursor = event.objectsUnderCursor;

    const newHoveredObject =
      objectsUnderCursor.length > 0 ? objectsUnderCursor[0] : null;

    // Fire 'mouseenter' and 'mouseleave' events ('hovering')
    if (this.hoveredObject != null && this.hoveredObject != newHoveredObject) {
      // Fire mouseleave event on the previously hovered object
      this.hoveredObject.userData.vueObject.$emit(
        "mouseleave",
        new Event("mouseleave")
      );
    }

    if (newHoveredObject != null && newHoveredObject != this.hoveredObject) {
      // Fire mouseenter event on the newly hovered object
      newHoveredObject.userData.vueObject.$emit(
        "mouseenter",
        new Event("mouseenter")
      );
    }
    this.hoveredObject = newHoveredObject;

    // Cancel further event handling if a handler has captured the event
    if (event.event.defaultPrevented) {
      return;
    }

    // Event forwarding to the object under the cursor
    if (this.hoveredObject) {
      this.hoveredObject.userData.vueObject.$emit(type, event.event);
    }
  }
}
