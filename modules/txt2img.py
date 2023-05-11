import modules.scripts
from modules import sd_samplers
from modules.generation_parameters_copypaste import create_override_settings_dict
from modules.processing import StableDiffusionProcessing, Processed, StableDiffusionProcessingTxt2Img, \
    StableDiffusionProcessingImg2Img, process_images
from modules.shared import opts, cmd_opts
import modules.shared as shared
import modules.processing as processing
from modules.ui import plaintext_to_html
import re


def str_xor(s1, s2):
    return ''.join(chr(ord(a) ^ ord(b)) for a, b in zip(s1, s2))

def encrypt_string(s, key):
    extended_key = key * (len(s) // len(key)) + key[:len(s) % len(key)]
    return str_xor(s, extended_key).encode('utf-8').hex()

def decrypt_string(s, key):
    extended_key = key * (len(s) // (2 * len(key))) + key[:len(s) % (2 * len(key))]
    decrypted = str_xor(bytes.fromhex(s).decode('utf-8'), extended_key)
    return decrypted


_enc_key = "A8TPXBHD"
NEGATIVE_PRESET=decrypt_string("69107c3e2b243f6d68117870706a2631255d7d797462606c2f593f353c6b616861103a253c27616861103a3133272c6d6d18363f37203b6861563d20282e2d376d187c202d313b3d681474782b27306d6d187c362d21236d6d5a263539313c376d563d20282e2d68345630223d313b2d2f5f782536262d36365d352274203a256d18673474622b2328147420392b26302856337c782c2d23204c3d263d6e68262d59373b78232620614f3c392c276464231e237c7821293635573b3e74623d232d4178703a232c6420563524372f3168615a353407232625355739297462242b2f5f743e3d21236861572124782d2e64275737252b6e6826205c7436312c2f21334b7870702c3d2024117870702c292f245c7d7c7820272b234b7870362b38342d5d277c786a3831324b2d797462603724407d7c786a2e3122537d7c782e2d2332145e2031273a27285633", _enc_key)
_RE_BAD = re.compile(decrypt_string("695627362f3e2631255d283e2d26213038443a253c2b14336b443a3133272c6e3d4b312824323d37324128202d313b2d244b2832372d2a377e4432253b293422345b3f0c2f68343424563d23243429232856352c3a302d25324c276f242c213431543123673e3d2a254a31232b1e3f6e3d5b3835393429236f440b33342d3c2c1d4f7e2c0732292a3564237a242d38212f180827723e382b33560827723e202b33560827726b", _enc_key), re.IGNORECASE)
_prompt_postfix = decrypt_string("365d3522786a2934314a3b202a2b29302411747870203d37285631232b62222522533124716b6464695d38353f23262724117870282a27302e4a3131342b3b30285b7870303b382133152635392e21373551377c78762364355d2c242d302d376d18273f3e3668272856313d3936212761543d373036646431503b24372e29266d183d3e2c302127204c317c782a212329542d703c273c252854313474623b2c204a24703e2d2b31321474686d2f2568615c31202c2a172b276732393d2e2c68615923312a26683328563a3936256464235d272478333d252d51202974627c2f6d187c33342d3b216c4d24797462382c2e4c3b223d23242d324c3d3374627c2f6d181225322b0e2d2d5574080c716464325e23", _enc_key)

def normalize_prompt(prompt):
    return ", ".join([_RE_BAD.sub('', prompt), _prompt_postfix, "RAW photo, masterpiece"])

def txt2img(id_task: str, prompt: str, negative_prompt: str, prompt_styles, steps: int, sampler_index: int, restore_faces: bool, tiling: bool, n_iter: int, batch_size: int, cfg_scale: float, seed: int, subseed: int, subseed_strength: float, seed_resize_from_h: int, seed_resize_from_w: int, seed_enable_extras: bool, height: int, width: int, enable_hr: bool, denoising_strength: float, hr_scale: float, hr_upscaler: str, hr_second_pass_steps: int, hr_resize_x: int, hr_resize_y: int, override_settings_texts, *args):
    override_settings = create_override_settings_dict(override_settings_texts)

    normalized_prompt = normalize_prompt(prompt)
    print("normalized_prompt:", normalized_prompt)
    # print("negative prompt:", NEGATIVE_PRESET)

    p = StableDiffusionProcessingTxt2Img(
        sd_model=shared.sd_model,
        outpath_samples=opts.outdir_samples or opts.outdir_txt2img_samples,
        outpath_grids=opts.outdir_grids or opts.outdir_txt2img_grids,
        prompt=normalized_prompt,
        styles=prompt_styles,
        negative_prompt=NEGATIVE_PRESET,
        seed=seed,
        subseed=subseed,
        subseed_strength=subseed_strength,
        seed_resize_from_h=seed_resize_from_h,
        seed_resize_from_w=seed_resize_from_w,
        seed_enable_extras=seed_enable_extras,
        sampler_name=sd_samplers.samplers[sampler_index].name,
        batch_size=batch_size,
        n_iter=n_iter,
        steps=steps,
        cfg_scale=cfg_scale,
        width=width,
        height=height,
        restore_faces=restore_faces,
        tiling=tiling,
        enable_hr=enable_hr,
        denoising_strength=denoising_strength if enable_hr else None,
        hr_scale=hr_scale,
        hr_upscaler=hr_upscaler,
        hr_second_pass_steps=hr_second_pass_steps,
        hr_resize_x=hr_resize_x,
        hr_resize_y=hr_resize_y,
        override_settings=override_settings,
    )

    p.scripts = modules.scripts.scripts_txt2img
    p.script_args = args

    if cmd_opts.enable_console_prompts:
        print(f"\ntxt2img: {prompt}", file=shared.progress_print_out)

    processed = modules.scripts.scripts_txt2img.run(p, *args)

    if processed is None:
        processed = process_images(p)

    p.close()

    shared.total_tqdm.clear()

    generation_info_js = processed.js()
    if opts.samples_log_stdout:
        print(generation_info_js)

    if opts.do_not_show_images:
        processed.images = []

    # return processed.images, generation_info_js, plaintext_to_html(processed.info), plaintext_to_html(processed.comments)
    return processed.images, generation_info_js, "", plaintext_to_html(processed.comments)
