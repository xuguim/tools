import { createApp, h } from 'vue';
import ElementPlus from 'element-plus';
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import App from './dev-tools.vue'

import 'element-plus/dist/index.css'
import 'diff2html/bundles/css/diff2html.min.css';


frappe.devTools = class devTools {
	constructor({wrapper},page) {
		this.wrapper = wrapper;
		this.page = page;
		this.init()
	}

	init() {
		this.wrapper[0].innerHTML = `
			<div id="app"></div>`
		const app = createApp(App);

		app.use(ElementPlus, {
			locale: zhCn,
		});

		app.mount('.page-container');
	}
}