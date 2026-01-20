#!/usr/bin/env bash
# Credit: https://gitlab.gnome.org/World/Upscaler/-/blob/main/update_translation.sh?ref_type=heads

export PROJECT_NAME="warehouse"
export BUILD_DIR="translation-build/"
export PO_DIR="po/"
export LINGUAS_FILE="${PO_DIR}LINGUAS"
export POTFILES_FILE="${PO_DIR}POTFILES"


# Cleanup on exit, whether early or normal
cleanup() {
	unset PROJECT_NAME
	unset BUILD_DIR
	unset PO_DIR
	unset LINGUAS_FILE
	unset POTFILES_FILE
}
trap cleanup EXIT


# Update the POTFILES file
./update_potfiles.py
if [ $? -ne 0 ]; then
	echo "Error: update_potfiles.py failed. Exiting."
	exit 1
fi


# Update the LINGUAS file
rm "${LINGUAS_FILE}"
for po_file in "${PO_DIR}"*.po; do
	lang=$(basename "${po_file}" .po)
	echo "${lang}" >> "${LINGUAS_FILE}"
	echo "Wrote ${lang} to ${LINGUAS_FILE}"
done
echo -e "Updated ${LINGUAS_FILE}\n"


# Update the translation template
if [ -d "${BUILD_DIR}" ]; then
	rm -r "${BUILD_DIR}"
fi
meson "${BUILD_DIR}"
meson compile -C "${BUILD_DIR}" "${PROJECT_NAME}-pot"
rm -r "${BUILD_DIR}"
