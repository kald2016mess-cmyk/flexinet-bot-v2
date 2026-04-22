import { Router, type IRouter } from "express";
import healthRouter from "./health";
import miniappRouter from "./miniapp";
import { buildMiniappHtml } from "./miniapp-html";

const router: IRouter = Router();

router.use(healthRouter);
router.use("/miniapp", miniappRouter);

router.get("/app", (_req, res) => {
  res.setHeader("Content-Type", "text/html; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  res.send(buildMiniappHtml({ adsgramBlockId: process.env.ADSGRAM_BLOCK_ID }));
});

export default router;
