import { WebWorkerMLCEngineHandler } from "https://esm.run/@mlc-ai/web-llm"

const handler = new WebWorkerMLCEngineHandler()

self.onmessage = (msg) => {
  handler.onmessage(msg)
}



// // import { WebWorkerMLCEngineHandler } from "https://cdn.jsdelivr.net/npm/@mlc-ai/web-llm@0.2.46/+esm" // Descomentar para usar el modelo de 5.1 GB

// const handler = new WebWorkerMLCEngineHandler()

// self.onmessage = (msg) => {
//   handler.onmessage(msg)
// }