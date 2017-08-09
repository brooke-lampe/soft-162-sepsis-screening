package edu.sepsis.cse.soft162;

import org.kivy.android.PythonActivity;
import android.content.Intent;
import android.net.Uri;
import android.app.Activity;

public class Reminder {
    public static boolean remind() {
        Intent intent = new Intent(Intent.ACTION_INSERT);

        Activity activity = PythonActivity.mActivity;
        if (intent.resolveActivity(activity.getPackageManager()) != null) {
            activity.startActivity(intent);
            return true;
        }
        return false;
    }
}
