import type { RouteLocation } from "vue-router";
import PcbEntityList from "@/components/editor/entity-views/PcbEntityList.vue";
import PcbEntityDetails from "@/components/editor/entity-views/PcbEntityDetails.vue";
import UartTerminal from "@/components/editor/forms/UartTerminal.vue";
import ScanCreateForm from "@/components/editor/forms/ScanCreateForm.vue";
import ScanAnalysisForm from "@/components/editor/forms/ScanAnalysisForm.vue";
import NetworkReversingForm from "@/components/editor/forms/NetworkReversingForm.vue";
import VoltageMeasurementForm from "@/components/editor/forms/VoltageMeasurementForm.vue";

export const routes = [
  {
    path: "",
    name: "pcb-detail",
    components: {
      default: PcbEntityList,
      detail: PcbEntityDetails,
    },
  },
  {
    path: "scan/new",
    name: "scan-new",
    component: ScanCreateForm,
    props: (route: RouteLocation) => ({
      pcbId: Number.parseInt(route.params.pcbId[0]),
    }),
  },
  {
    path: "scan/analysis",
    name: "scan-analysis",
    component: ScanAnalysisForm,
    props: (route: RouteLocation) => ({
      pcbId: Number.parseInt(route.params.pcbId[0]),
    }),
  },
  {
    path: "network-reversing",
    name: "network-reversing",
    component: NetworkReversingForm,
  },
  {
    path: "voltage-measurement",
    name: "voltage-measurement",
    component: VoltageMeasurementForm,
    props: (route: RouteLocation) => ({
      pcbId: Number.parseInt(route.params.pcbId[0]),
    }),
  },
  {
    path: "uart-terminal",
    name: "uart-terminal",
    component: UartTerminal,
    props: (route: RouteLocation) => ({
      pcbId: Number.parseInt(route.params.pcbId[0]),
      rxPinId: Number.parseInt(route.query.rx as string),
      txPinId: Number.parseInt(route.query.tx as string),
      baudrate: Number.parseInt(route.query.baudrate as string),
    }),
  },
];
