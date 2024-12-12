<template>
	<div class="m-2 p-2 rounded border shadow " style="min-height:90vh;">
		<div class="flex">
			<el-select v-model="selectapp" @change="appChange($event)" style="width: 300px;padding-right: 6px;"
				clearable filterable :placeholder="t('Select') + t('App Name')">
				<el-option v-for="app in apps" :key="app" :value="app" />
			</el-select>
			<el-select v-if="selectapp" v-model="selectModule" @change="moduleChange($event)"
				style="width: 300px;padding-right: 6px;" clearable filterable :placeholder="t('Select') + t('Module')">
				<el-option v-for="module in modules" :key="module" :value="module" />
			</el-select>
			<el-select v-if="selectModule" v-model="selectDoctype" @change="doctypeChange($event)"
				style="width: 300px;padding-right: 6px;" clearable filterable :placeholder="t('Select') + t('Doctype')">
				<el-option v-for="doctype in doctypes" :key="doctype" :value="doctype" :label="t(doctype)" />
			</el-select>
		</div>

		<div class="flex align-items-end">
			<div v-for="(value, key) in show_details">
				<el-badge v-if="file_data[key]?.length > 0" :value="file_data[key]?.length" class="badge"
					:offset="[-5, 5]">
					<el-switch v-model="show_details[key]" inline-prompt size="large" :active-text="t(lables[key])"
						:inactive-text="t(lables[key])" />
				</el-badge>
			</div>
			<el-switch v-if="selectDoctype" v-model="showModified" inline-prompt size="large" @change="draw_diff"
				:active-text="t('Show') + t('Last Modified On')" :inactive-text="t('Hide') + t('Last Modified On')" />
		</div>


		<div class="border rounded my-4 p-2 shadow-sm" v-show="custom_fields_names.length > 0">
			<div v-if="selectDoctype" v-show="show_details.custom_fields && !loading" class="bold text-center my-4">
				{{ t('Custom Field') }}</div>
			<div v-if="selectDoctype" v-show="show_details.custom_fields && !loading">
				<div v-for="field_name in custom_fields_names">
					<div :id="field_name"></div>
				</div>
			</div>
		</div>

		<div class="border rounded my-4 p-2 shadow-sm" v-show="custom_property_setters_names.length > 0">
			<div v-if="selectDoctype" v-show="show_details.property_setters && !loading" class="bold text-center my-4">
				{{ t('Property Setter') }}</div>
			<div v-if="selectDoctype" v-show="show_details.property_setters && !loading">
				<div v-for="prop_name in custom_property_setters_names">
					<div :id="prop_name"></div>
				</div>
			</div>
		</div>



	</div>
</template>
<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue';
import { createPatch } from 'diff'
import { Diff2HtmlUI } from 'diff2html/lib/ui/js/diff2html-ui'

// basic data
const apps = ref([]);
const modules = ref([]);
const doctypes = ref([]);
const selectapp = ref('');
const selectModule = ref('');
const selectDoctype = ref('');
const showModified = ref(true);

// custom file from app
const file_data = reactive({});
const res = reactive({});
const data = reactive({});
const show_details = ref({
	'custom_fields': true,
	'property_setters': true,
	'custom_perms': true,
	'links': true
})
const current_custom_fields = ref([]);
const current_property_setters = ref([]);


// for diff
const loading = ref(false)
const custom_fields_names = ref([])
const custom_property_setters_names = ref([])

const lables = {
	'custom_fields': 'Custom Field',
	'property_setters': 'Property Setter',
	'custom_perms': 'Custom Permissions',
	'links': 'Links'
}


const reset_data = () => {
	selectModule.value = '';
	selectDoctype.value = '';
	current_custom_fields.value = [];
	current_property_setters.value = [];
	for (const type of ['custom_fields', 'property_setters', 'custom_perms', 'links']) {
		file_data[type] = undefined
	};
}
const appChange = (e) => {
	selectModule.value = '';
	selectDoctype.value = '';
	get_customize_data()
	reset_data();
	if (!e) return;
	modules.value = res[e].modules;

};
const moduleChange = (e) => {
	doctypes.value = []
	selectDoctype.value = '';
	let file = res[selectapp.value].files[e]
	for (const key in file) {
		if (file.hasOwnProperty(key)) {
			data[key] = file[key];
			doctypes.value.push(file[key].doctype);
		}
	}
}
const doctypeChange = (e) => {

	loading.value = true
	let doctype_file = res[selectapp.value].files[selectModule.value].filter(item => {
		return item.doctype == e
	})
	if (doctype_file.length == 0) return
	doctype_file = doctype_file[0]
	for (const key in doctype_file) {
		if (doctype_file.hasOwnProperty(key)) {
			file_data[key] = doctype_file[key];
		}
	}
	get_doctype_custom_field(e)
}
const get_doctype_custom_field = (doctype) => {
	frappe.call({
		method: "tools.api.get_custom_fields_and_prop_setter",
		args: {
			app_name: selectapp.value,
			doctype: doctype
		},
		callback: function (r) {
			if (r.message) {
				current_custom_fields.value = r.message.custom_fields;
				current_property_setters.value = r.message.property_setters;
				get_doctype_costom_names();
			}
		}
	})

}


const get_doctype_costom_names = () => {
	if (file_data.custom_fields?.length > 0) {
		custom_fields_names.value = file_data.custom_fields.map(item => {
			return custom_fields_names.value.includes(item.name) && !item.name.includes('main-field_order') ? null : item.name;
		})
	}
	if (file_data.property_setters?.length > 0) {
		custom_property_setters_names.value = file_data.property_setters.map(item => {
			return custom_property_setters_names.value.includes(item.name) ? null : item.name;
		})
	}

	nextTick(() => {
		// Waiting for rendering completed
		draw_diff();
		loading.value = false
	});

}

const draw_diff = () => {
	if (custom_fields_names.value.length > 0) {
		custom_fields_names.value.forEach(item => {
			// file_data.custom_fields.forEach(field => {
			// 	build_html(item, 'custom_fields')
			// })
			build_html(item, 'custom_fields')

		})
	}
	if (custom_property_setters_names.value.length > 0) {
		custom_property_setters_names.value.forEach(item => {
			// file_data.property_setters.forEach(prop => {
			// 	build_html(item, 'property_setters')
			// })
			build_html(item, 'property_setters')
		})
	}





}

const build_html = (id, type) => {
	let file_doc = {}
	let custom_doc = {}
	if (type == 'custom_fields') {
		let ori_data = file_data.custom_fields.filter(item => {
			return item.name == id
		})
		file_doc = ori_data?.length > 0 ? remove_modified(ori_data[0]) : {};
		let new_data = current_custom_fields.value.filter(item => {
			return item.name == id
		})
		custom_doc = new_data?.length > 0 ? remove_modified(new_data[0]) : {};
	} else if (type == 'property_setters') {
		let ori_data = file_data.property_setters.filter(item => {
			return item.name == id
		})
		file_doc = ori_data?.length > 0 ? remove_modified(ori_data[0]) : {};
		let new_data = current_property_setters.value.filter(item => {
			return item.name == id
		})
		custom_doc = new_data?.length > 0 ? remove_modified(new_data[0]) : {};
	} else {
		return
	}


	const text1 = JSON.stringify(file_doc, null, 2);
	const text2 = JSON.stringify(custom_doc, null, 2);

	const diffString = createPatch('', text1, text2, file_doc.name || '', custom_doc.name || '');

	const targetElement = document.getElementById(id);
	const configuration = {
		drawFileList: false,
		fileListToggle: false,
		fileListStartVisible: false,
		fileContentToggle: false,
		matching: 'lines',
		outputFormat: 'side-by-side', //'line-by-line' or 'side-by-side'
		synchronisedScroll: true,
		highlight: true,
		renderNothingWhenEmpty: false,
	};
	const diff2htmlUi = new Diff2HtmlUI(targetElement, diffString, configuration);
	diff2htmlUi.draw();
	diff2htmlUi.highlightCode();
}
const remove_modified = (data) => {
	console.log(data)
	let res = {}

	Object.keys(data).reduce((acc, key) => {
		if(showModified.value == 1) {
			acc[key] = data[key] || null;
		}
		else if (key != 'modified') {
			acc[key] = data[key] || null;
		}

		return acc;
	},res)

	return res
}

const t = (txt) => {
	return __(txt, 'zh-CN')
}
const get_customize_data = () => {
	frappe.call({
		method: "tools.api.get_customize_data",
		args: {},
		callback: function (r) {
			if (r.message) {
				let data = r.message;
				for (const app in data) {
					if (data.hasOwnProperty(app)) {
						res[app] = data[app];
					}
				}
				apps.value = Object.keys(data);
			}
		}
	})
}
onMounted(() => {
	get_customize_data()
})

</script>
<style scoped>
.badge {
	margin-top: 10px;
	margin-right: 30px;
}
</style>