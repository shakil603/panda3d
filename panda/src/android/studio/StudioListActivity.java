/**
 * Panda3D Studio — list screens.
 *
 * Shows a list of items depending on the mode:
 *   "samples" — the bundled sample games (assets/games/*.py)
 *   "mine"    — the user's games (files in the app's private dir)
 *   "models"  — the bundled 3D models (assets/models/*.egg)
 *
 * Tapping a sample or a model runs it immediately.  Tapping one of "my
 * games" offers Run / Edit / Delete (tap or hold).
 */

package org.panda3d.studio;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.util.ArrayList;
import java.util.List;

public class StudioListActivity extends Activity
        implements View.OnClickListener,
                   AdapterView.OnItemClickListener,
                   AdapterView.OnItemLongClickListener {

    public static final String EXTRA_MODE = "mode";

    private String mode;
    private List<String> paths = new ArrayList<String>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        mode = getIntent().getStringExtra(EXTRA_MODE);
        if (mode == null) {
            mode = "samples";
        }

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(18, 27, 51));

        TextView title = new TextView(this);
        if (mode.equals("samples")) {
            title.setText("Sample Games");
        } else if (mode.equals("mine")) {
            title.setText("My Games");
        } else {
            title.setText("3D Models");
        }
        title.setTextColor(Color.WHITE);
        title.setTextSize(24);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setGravity(Gravity.CENTER_HORIZONTAL);
        title.setPadding(0, 24, 0, 12);
        root.addView(title);

        final List<String> displayNames = new ArrayList<String>();

        if (mode.equals("samples")) {
            fillFromAssets("games", ".py", displayNames);
            root.addView(makeHint("Tap a game to play it"));
        } else if (mode.equals("models")) {
            fillFromAssets("models", ".egg", displayNames);
            root.addView(makeHint("Tap a model to view it in 3D"));
        } else {
            // My games: real files in the app's private games directory.
            File dir = getGamesDir();
            if (!dir.exists()) {
                dir.mkdirs();
            }
            File[] files = dir.listFiles();
            if (files != null) {
                for (int i = files.length - 1; i >= 0; --i) {  // newest first
                    File f = files[i];
                    if (f.isFile() && f.getName().endsWith(".py")) {
                        displayNames.add(prettyName(f.getName()));
                        paths.add(f.getAbsolutePath());
                    }
                }
            }
            if (displayNames.isEmpty()) {
                displayNames.add("(no games yet)");
                paths.add("");
            }
            root.addView(makeHint("Tap to run  •  hold to edit or delete"));
        }

        if (mode.equals("mine")) {
            Button newBtn = new Button(this);
            newBtn.setText("+ New Game");
            newBtn.setAllCaps(false);
            newBtn.setTextSize(18);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT);
            lp.setMargins(24, 8, 24, 8);
            newBtn.setLayoutParams(lp);
            newBtn.setTag("new");
            newBtn.setOnClickListener(this);
            root.addView(newBtn);
        }

        ListView list = new ListView(this);
        list.setBackgroundColor(Color.rgb(26, 38, 68));
        ArrayAdapter<String> adapter = new ArrayAdapter<String>(
                this, android.R.layout.simple_list_item_1, displayNames);
        list.setAdapter(adapter);
        list.setOnItemClickListener(this);
        list.setOnItemLongClickListener(this);

        root.addView(list, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));

        setContentView(root);
    }

    private TextView makeHint(String text) {
        TextView t = new TextView(this);
        t.setText(text);
        t.setTextColor(Color.rgb(120, 140, 180));
        t.setTextSize(13);
        t.setGravity(Gravity.CENTER_HORIZONTAL);
        t.setPadding(0, 0, 0, 8);
        return t;
    }

    /** Lists files from the APK assets (they run via the VFS path). */
    private void fillFromAssets(String dir, String suffix,
                                List<String> names) {
        String[] files;
        try {
            files = getAssets().list(dir);
        } catch (Exception e) {
            Toast.makeText(this, "Cannot open assets: " + e,
                           Toast.LENGTH_LONG).show();
            files = new String[0];
        }
        for (String f : files) {
            if (f.endsWith(suffix)) {
                names.add(prettyName(f));
                paths.add("/android_asset/" + dir + "/" + f);
            }
        }
        if (names.isEmpty()) {
            names.add("(empty)");
            paths.add("");
        }
    }

    private File getGamesDir() {
        return new File(getFilesDir(), "games");
    }

    /** Creates a new game file from a template and returns its path. */
    private String createNewGame() {
        File dir = getGamesDir();
        if (!dir.exists()) {
            dir.mkdirs();
        }
        int n = 1;
        while (true) {
            File f = new File(dir, "game" + n + ".py");
            if (!f.exists()) {
                try {
                    Writer w = new OutputStreamWriter(
                            new FileOutputStream(f), "UTF-8");
                    w.write(StudioEditorActivity.NEW_GAME_TEMPLATE);
                    w.close();
                    return f.getAbsolutePath();
                } catch (Exception e) {
                    Toast.makeText(this, "Cannot create file: " + e,
                                   Toast.LENGTH_LONG).show();
                    return null;
                }
            }
            ++n;
        }
    }

    // ---- event handlers -------------------------------------------------

    @Override
    public void onClick(View v) {
        if ("new".equals(v.getTag())) {
            String path = createNewGame();
            if (path != null) {
                Intent i = new Intent(this, StudioEditorActivity.class);
                i.putExtra(StudioEditorActivity.EXTRA_PATH, path);
                startActivity(i);
            }
        }
    }

    @Override
    public void onItemClick(AdapterView<?> parent, View view,
                            int position, long id) {
        String path = paths.get(position);
        if (path.length() == 0) {
            return;  // placeholder
        }
        if (mode.equals("mine")) {
            showMyGameDialog(position, path);
        } else if (mode.equals("samples")) {
            runPython(path);
        } else {
            runPanda(path);
        }
    }

    @Override
    public boolean onItemLongClick(AdapterView<?> parent, View view,
                                   int position, long id) {
        String path = paths.get(position);
        if (mode.equals("mine") && path.length() > 0) {
            showMyGameDialog(position, path);
            return true;
        }
        return false;
    }

    private void showMyGameDialog(int position, String path) {
        new AlertDialog.Builder(this)
            .setTitle(prettyName(new File(path).getName()))
            .setItems(new String[] { "Run", "Edit", "Delete" },
                      new DialogHandler(this, position, path))
            .show();
    }

    /** Runs a Python game: real path or /android_asset VFS path. */
    void runPython(String path) {
        try {
            Intent i = new Intent(Intent.ACTION_VIEW,
                                  Uri.fromFile(new File(path)));
            i.setClassName(getPackageName(),
                           "org.panda3d.android.PythonActivity");
            startActivity(i);
        } catch (Exception e) {
            Toast.makeText(this, "Cannot start: " + e, Toast.LENGTH_LONG).show();
        }
    }

    /** Opens a 3D model in the Panda viewer. */
    void runPanda(String path) {
        try {
            Intent i = new Intent(Intent.ACTION_VIEW,
                                  Uri.fromFile(new File(path)));
            i.setClassName(getPackageName(),
                           "org.panda3d.android.PandaActivity");
            startActivity(i);
        } catch (Exception e) {
            Toast.makeText(this, "Cannot start: " + e, Toast.LENGTH_LONG).show();
        }
    }

    /** "star_catcher.py" -> "Star Catcher" */
    public static String prettyName(String filename) {
        String base = filename;
        int dot = base.lastIndexOf('.');
        if (dot > 0) {
            base = base.substring(0, dot);
        }
        StringBuilder sb = new StringBuilder();
        boolean upper = true;
        for (int i = 0; i < base.length(); ++i) {
            char c = base.charAt(i);
            if (c == '_' || c == '-') {
                upper = true;
            } else if (upper) {
                sb.append(Character.toUpperCase(c));
                upper = false;
            } else {
                sb.append(c);
            }
        }
        return sb.toString();
    }

    // ---- the Run / Edit / Delete dialog ----------------------------------

    /**
     * Named (not anonymous) inner class so the build system can list the
     * generated class file deterministically.
     */
    static class DialogHandler implements DialogInterface.OnClickListener {
        private final StudioListActivity host;
        private final String path;

        DialogHandler(StudioListActivity host, int position, String path) {
            this.host = host;
            this.path = path;
        }

        public void onClick(DialogInterface dialog, int which) {
            if (which == 0) {
                host.runPython(path);
            } else if (which == 1) {
                Intent i = new Intent(host, StudioEditorActivity.class);
                i.putExtra(StudioEditorActivity.EXTRA_PATH, path);
                host.startActivity(i);
            } else {
                new AlertDialog.Builder(host)
                    .setMessage("Delete this game?")
                    .setPositiveButton("Delete", new DeleteHandler(host, path))
                    .setNegativeButton("Cancel", null)
                    .show();
            }
        }
    }

    /** The delete-confirmation dialog's OK button. */
    static class DeleteHandler implements DialogInterface.OnClickListener {
        private final StudioListActivity host;
        private final String path;

        DeleteHandler(StudioListActivity host, String path) {
            this.host = host;
            this.path = path;
        }

        public void onClick(DialogInterface dialog, int which) {
            if (!new File(path).delete()) {
                Toast.makeText(host, "Delete failed",
                               Toast.LENGTH_SHORT).show();
            }
            host.finish();  // refresh the list
        }
    }
}
